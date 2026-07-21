frappe.pages['wafd-document-studio'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({parent: wrapper, title: __('WAFD Document Studio'), single_column: true});
  new WAFDDocumentStudio(page, wrapper);
};

class WAFDDocumentStudio {
  constructor(page, wrapper) {
    this.page = page;
    this.wrapper = $(wrapper);
    this.template = null;
    this.blocks = [];
    this.selected = null;
    this.dirty = false;
    this.zoom = 0.75;
    this.grid = 10;
    this.snap = true;
    this.clipboard = null;
    this.render();
    this.bind();
    this.load_templates();
  }

  render() {
    this.wrapper.find('.layout-main-section').html(`
      <div class="wds-topbar">
        <select class="form-control wds-template"></select>
        <button class="btn btn-default btn-sm wds-new">${__('New Template')}</button>
        <button class="btn btn-primary btn-sm wds-save">${__('Save')}</button>
        <button class="btn btn-default btn-sm wds-preview">${__('Preview')}</button>
        <button class="btn btn-default btn-sm wds-pdf">${__('PDF')}</button>
        <span class="wds-separator"></span>
        <button class="btn btn-default btn-sm wds-duplicate" title="${__('Duplicate')}">⧉</button>
        <button class="btn btn-default btn-sm wds-front" title="${__('Bring Forward')}">↑</button>
        <button class="btn btn-default btn-sm wds-back" title="${__('Send Backward')}">↓</button>
        <button class="btn btn-default btn-sm wds-lock" title="${__('Lock / Unlock')}">🔒</button>
        <button class="btn btn-default btn-sm wds-delete-top" title="${__('Delete')}">⌫</button>
        <span class="wds-separator"></span>
        <label class="wds-inline-check"><input type="checkbox" class="wds-snap" checked> ${__('Snap')}</label>
        <select class="form-control wds-zoom">
          <option value="0.5">50%</option><option value="0.75" selected>75%</option><option value="1">100%</option><option value="1.25">125%</option><option value="1.5">150%</option>
        </select>
        <span class="wds-status"></span>
      </div>
      <div class="wds-shell">
        <aside class="wds-panel wds-left-panel">
          <h4>${__('Elements')}</h4>
          <div class="wds-tools-grid">
            ${this.tool('text',__('Text'),'T')}${this.tool('field',__('Dynamic Field'),'{}')}${this.tool('image',__('Image'),'▧')}${this.tool('logo',__('Logo'),'W')}${this.tool('stamp',__('Stamp'),'◉')}${this.tool('signature',__('Signature'),'✎')}${this.tool('line',__('Line'),'—')}${this.tool('table',__('Table'),'▦')}${this.tool('qr',__('QR Placeholder'),'▣')}
          </div>
          <hr>
          <h4>${__('Document Fields')}</h4>
          <input class="form-control wds-field-search" placeholder="${__('Search fields')}">
          <div class="wds-fields"><div class="wds-empty">${__('Select a template')}</div></div>
        </aside>
        <main class="wds-panel wds-stage-wrap">
          <div class="wds-ruler-corner"></div><div class="wds-ruler-x"></div><div class="wds-ruler-y"></div>
          <div class="wds-stage"><div class="wds-page"></div></div>
        </main>
        <aside class="wds-panel wds-right-panel">
          <h4>${__('Element Properties')}</h4>
          <div class="wds-properties"><div class="wds-empty">${__('Select an element')}</div></div>
          <hr><h4>${__('Page Settings')}</h4>
          <div class="wds-page-properties"></div>
        </aside>
      </div>`);
  }

  tool(type, label, icon) {
    return `<button class="wds-tool" data-type="${type}" draggable="true"><span>${icon}</span><small>${label}</small></button>`;
  }

  bind() {
    this.wrapper.on('click', '.wds-tool', e => this.add_block($(e.currentTarget).data('type')));
    this.wrapper.on('dragstart', '.wds-tool', e => e.originalEvent.dataTransfer.setData('text/wds-type', $(e.currentTarget).data('type')));
    this.wrapper.on('dragover', '.wds-page', e => e.preventDefault());
    this.wrapper.on('drop', '.wds-page', e => {
      e.preventDefault();
      const type = e.originalEvent.dataTransfer.getData('text/wds-type');
      if (!type) return;
      const rect = e.currentTarget.getBoundingClientRect();
      this.add_block(type, (e.originalEvent.clientX - rect.left) / this.zoom, (e.originalEvent.clientY - rect.top) / this.zoom);
    });
    this.wrapper.on('click', '.wds-new', () => this.new_template());
    this.wrapper.on('click', '.wds-save', () => this.save());
    this.wrapper.on('click', '.wds-preview', () => this.preview());
    this.wrapper.on('click', '.wds-pdf', () => this.pdf());
    this.wrapper.on('click', '.wds-duplicate', () => this.duplicate_selected());
    this.wrapper.on('click', '.wds-front', () => this.layer(1));
    this.wrapper.on('click', '.wds-back', () => this.layer(-1));
    this.wrapper.on('click', '.wds-lock', () => this.toggle_lock());
    this.wrapper.on('click', '.wds-delete-top', () => this.delete_selected());
    this.wrapper.on('change', '.wds-template', e => this.load_template(e.target.value));
    this.wrapper.on('click', '.wds-field-chip', e => this.add_field($(e.currentTarget).data('field')));
    this.wrapper.on('input', '.wds-field-search', e => this.filter_fields(e.target.value));
    this.wrapper.on('change', '.wds-zoom', e => { this.zoom = Number(e.target.value); this.apply_zoom(); });
    this.wrapper.on('change', '.wds-snap', e => { this.snap = e.target.checked; this.render_page(); });
    this.wrapper.on('input change', '.wds-page-properties input,.wds-page-properties select', () => this.update_page());
    this.wrapper.on('click', '.wds-page', e => { if (e.target === e.currentTarget) this.select(null); });
    $(document).on('keydown.wds', e => this.on_keydown(e));
    window.addEventListener('beforeunload', e => { if (this.dirty) { e.preventDefault(); e.returnValue = ''; } });
  }

  on_keydown(e) {
    if (!this.wrapper.is(':visible')) return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (['input','textarea','select'].includes(tag) || e.target.isContentEditable) return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') { e.preventDefault(); this.save(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'd') { e.preventDefault(); this.duplicate_selected(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c') { e.preventDefault(); this.copy_selected(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') { e.preventDefault(); this.paste_selected(); }
    else if (['Delete','Backspace'].includes(e.key)) { e.preventDefault(); this.delete_selected(); }
    else if (this.selected && ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)) {
      e.preventDefault(); const b = this.get(this.selected); if (!b || b.locked) return;
      const step = e.shiftKey ? 10 : 1;
      if (e.key === 'ArrowLeft') b.x -= step; if (e.key === 'ArrowRight') b.x += step;
      if (e.key === 'ArrowUp') b.y -= step; if (e.key === 'ArrowDown') b.y += step;
      b.x = Math.max(0,b.x); b.y = Math.max(0,b.y); this.render_page(); this.select(b.id); this.mark_dirty();
    }
  }

  async load_templates() {
    const r = await frappe.call('wafd_one.document_studio.list_templates');
    const rows = r.message || [];
    const sel = this.wrapper.find('.wds-template').empty().append(`<option value="">${__('Select Template')}</option>`);
    rows.forEach(x => sel.append(`<option value="${frappe.utils.escape_html(x.name)}">${frappe.utils.escape_html(x.template_title)} — ${frappe.utils.escape_html(x.reference_doctype)}</option>`));
    const route = frappe.route_options || {}; frappe.route_options = null;
    if (route.template) { sel.val(route.template); this.load_template(route.template); }
  }

  async load_template(name) {
    if (!name) return;
    const r = await frappe.call('wafd_one.document_studio.get_template', {template_name:name});
    this.template = r.message;
    this.blocks = (this.template.canvas && this.template.canvas.blocks) || [];
    this.render_page(); this.render_fields(); this.render_page_properties();
    this.dirty = false; this.status(__('Loaded'));
  }

  snap_value(value) { return this.snap ? Math.round(value / this.grid) * this.grid : Math.round(value); }

  render_page() {
    const t = this.template || {};
    const sizes = {A4:[210,297], A5:[148,210], Letter:[216,279]};
    let mm = sizes[t.page_size] || sizes.A4;
    if (t.orientation === 'Landscape') mm = [mm[1], mm[0]];
    const width = mm[0] * 3.78, height = mm[1] * 3.78;
    const margins = {
      top: Math.max(0, Number(t.margin_top_mm || 0)) * 3.78,
      right: Math.max(0, Number(t.margin_right_mm || 0)) * 3.78,
      bottom: Math.max(0, Number(t.margin_bottom_mm || 0)) * 3.78,
      left: Math.max(0, Number(t.margin_left_mm || 0)) * 3.78
    };
    const page = this.wrapper.find('.wds-page').css({width:`${width}px`,height:`${height}px`,direction:(t.direction||'RTL').toLowerCase()}).empty();
    page.append(`<div class="wds-margin-guide" style="top:${margins.top}px;right:${margins.right}px;bottom:${margins.bottom}px;left:${margins.left}px"></div>`);
    page.toggleClass('wds-grid-enabled', this.snap);
    this.blocks.forEach(b => page.append(this.block_html(b)));
    this.bind_blocks(); this.apply_zoom(); this.render_rulers(width,height);
  }

  apply_zoom() { this.wrapper.find('.wds-page').css('transform', `scale(${this.zoom})`); this.wrapper.find('.wds-stage').css({width:`${(this.wrapper.find('.wds-page').outerWidth()||0)*this.zoom+80}px`,height:`${(this.wrapper.find('.wds-page').outerHeight()||0)*this.zoom+80}px`}); }

  render_rulers(width,height) {
    const x = this.wrapper.find('.wds-ruler-x').empty(), y = this.wrapper.find('.wds-ruler-y').empty();
    for (let i=0;i<=width;i+=37.8) x.append(`<span style="left:${i*this.zoom}px">${Math.round(i/3.78)}</span>`);
    for (let i=0;i<=height;i+=37.8) y.append(`<span style="top:${i*this.zoom}px">${Math.round(i/3.78)}</span>`);
  }

  block_html(b) {
    const font = b.font_family || 'Arial'; const fontSize = Number(b.font_size || 14); const color = b.color || '#111111';
    const bg = b.background || 'transparent'; const opacity = b.opacity == null ? 1 : Number(b.opacity); const rotate = Number(b.rotation || 0);
    const style = `left:${b.x}px;top:${b.y}px;width:${b.w}px;height:${b.h}px;z-index:${b.z||1};font-family:${font};font-size:${fontSize}px;color:${color};background:${bg};opacity:${opacity};transform:rotate(${rotate}deg);${b.bold?'font-weight:700;':''}${b.italic?'font-style:italic;':''}${b.underline?'text-decoration:underline;':''}${b.style||''}`;
    let content='';
    if (['image','logo','stamp','signature'].includes(b.type)) content = b.src ? `<img src="${frappe.utils.escape_html(b.src)}" style="width:100%;height:100%;object-fit:contain">` : `<div class="wds-empty">${__(b.type)}</div>`;
    else if (b.type==='line') content='<div style="border-top:1px solid currentColor;margin-top:50%"></div>';
    else if (b.type==='table') content=b.html || '<table style="width:100%;border-collapse:collapse"><tr><th style="border:1px solid #333">Item</th><th style="border:1px solid #333">Value</th></tr><tr><td style="border:1px solid #333">...</td><td style="border:1px solid #333">...</td></tr></table>';
    else if (b.type==='qr') content='<div style="border:1px solid #333;width:100%;height:100%;display:flex;align-items:center;justify-content:center">QR</div>';
    else content=b.html||__('Double click to edit');
    const editable=['text','field','table'].includes(b.type) && !b.locked ? 'contenteditable="true"' : '';
    return `<div class="wds-block ${b.locked?'locked':''}" data-id="${b.id}" style="${style}"><div class="wds-content" ${editable}>${content}</div><span class="wds-lock-badge">🔒</span><span class="wds-resizer"></span></div>`;
  }

  bind_blocks() {
    const self=this;
    this.wrapper.find('.wds-block').each(function(){
      const el=this,id=$(this).data('id'), b=self.get(id);
      el.addEventListener('pointerdown',e=>{
        if ($(e.target).hasClass('wds-resizer') || e.target.isContentEditable) return;
        self.select(id); if (b.locked) return;
        const sx=e.clientX,sy=e.clientY,ox=b.x,oy=b.y; el.setPointerCapture(e.pointerId);
        const move=ev=>{const pw=self.wrapper.find('.wds-page').width(),ph=self.wrapper.find('.wds-page').height();b.x=Math.max(0,Math.min(pw-b.w,self.snap_value(ox+(ev.clientX-sx)/self.zoom)));b.y=Math.max(0,Math.min(ph-b.h,self.snap_value(oy+(ev.clientY-sy)/self.zoom)));el.style.left=b.x+'px';el.style.top=b.y+'px';self.mark_dirty()};
        const up=()=>{el.removeEventListener('pointermove',move);el.removeEventListener('pointerup',up);self.render_properties()};
        el.addEventListener('pointermove',move);el.addEventListener('pointerup',up);
      });
      const resizer=$(this).find('.wds-resizer')[0];
      resizer.addEventListener('pointerdown',e=>{
        e.stopPropagation(); self.select(id); if (b.locked) return;
        const sx=e.clientX,sy=e.clientY,ow=b.w,oh=b.h; e.target.setPointerCapture(e.pointerId);
        const move=ev=>{const pw=self.wrapper.find('.wds-page').width(),ph=self.wrapper.find('.wds-page').height();b.w=Math.max(25,Math.min(pw-b.x,self.snap_value(ow+(ev.clientX-sx)/self.zoom)));b.h=Math.max(20,Math.min(ph-b.y,self.snap_value(oh+(ev.clientY-sy)/self.zoom)));el.style.width=b.w+'px';el.style.height=b.h+'px';self.mark_dirty()};
        const up=()=>{e.target.removeEventListener('pointermove',move);e.target.removeEventListener('pointerup',up);self.render_properties()};
        e.target.addEventListener('pointermove',move);e.target.addEventListener('pointerup',up);
      });
      $(this).find('.wds-content').on('input',function(){b.html=this.innerHTML;self.mark_dirty()});
    });
  }

  add_block(type, x=40, y=40) {
    if(!this.template) return frappe.msgprint(__('Select or create a template first.'));
    const id='b'+Date.now()+Math.floor(Math.random()*1000);
    const map={text:{w:300,h:60,html:__('Editable text')},field:{w:260,h:40,html:'{{ doc.name }}'},image:{w:150,h:100},logo:{w:180,h:90,src:this.template.logo},stamp:{w:130,h:130,src:this.template.stamp},signature:{w:160,h:80,src:this.template.signature},line:{w:400,h:20},table:{w:450,h:100},qr:{w:100,h:100}};
    this.blocks.push({id,type,x:this.snap_value(x),y:this.snap_value(y),w:map[type].w,h:map[type].h,html:map[type].html||'',src:map[type].src||'',z:this.max_z()+1,style:'',font_family:'Arial',font_size:14,color:'#111111',background:'transparent',opacity:1,rotation:0,bold:false,italic:false,underline:false,locked:false});
    this.render_page();this.select(id);this.mark_dirty();
  }

  add_field(field){this.add_block('field');const b=this.blocks[this.blocks.length-1];b.html=`{{ doc.get("${field}") or "" }}`;this.render_page();this.select(b.id)}
  select(id){this.selected=id;this.wrapper.find('.wds-block').removeClass('selected');if(id)this.wrapper.find(`.wds-block[data-id="${id}"]`).addClass('selected');this.render_properties()}
  get(id){return this.blocks.find(x=>x.id===id)}
  max_z(){return Math.max(0,...this.blocks.map(x=>Number(x.z||0)))}

  render_properties(){
    const box=this.wrapper.find('.wds-properties');
    if(!this.selected) return box.html(`<div class="wds-empty">${__('Select an element')}</div>`);
    const b=this.get(this.selected);
    box.html(`
      <div class="wds-prop-row">${this.prop('x','X',b.x,'number')}${this.prop('y','Y',b.y,'number')}</div>
      <div class="wds-prop-row">${this.prop('w',__('Width'),b.w,'number')}${this.prop('h',__('Height'),b.h,'number')}</div>
      <div class="wds-prop-row">${this.prop('z',__('Layer'),b.z,'number')}${this.prop('rotation',__('Rotation'),b.rotation||0,'number')}</div>
      ${this.select_prop('font_family',__('Font'),b.font_family||'Arial',['Arial','Tahoma','Times New Roman','Noto Naskh Arabic'])}
      <div class="wds-prop-row">${this.prop('font_size',__('Font Size'),b.font_size||14,'number')}${this.prop('opacity',__('Opacity'),b.opacity==null?1:b.opacity,'number','0.1')}</div>
      <div class="wds-prop-row">${this.prop('color',__('Text Color'),b.color||'#111111','color')}${this.prop('background',__('Background'),b.background||'#ffffff','color')}</div>
      <div class="wds-format-buttons"><button data-format="bold" class="${b.bold?'active':''}"><b>B</b></button><button data-format="italic" class="${b.italic?'active':''}"><i>I</i></button><button data-format="underline" class="${b.underline?'active':''}"><u>U</u></button></div>
      ${['image','logo','stamp','signature'].includes(b.type)?this.prop('src',__('Image URL'),b.src||'','text'):''}
      ${this.prop('style',__('Advanced CSS'),b.style||'','textarea')}
      <label class="wds-inline-check"><input type="checkbox" data-key="locked" ${b.locked?'checked':''}> ${__('Lock element')}</label>
      <button class="btn btn-danger btn-sm wds-delete">${__('Delete')}</button>`);
    const self=this;
    box.find('input,textarea,select').on('input change',function(){const key=$(this).data('key');if(!key)return;b[key]=$(this).attr('type')==='checkbox'?this.checked:($(this).attr('type')==='number'?Number(this.value):this.value);self.render_page();self.select(b.id);self.mark_dirty()});
    box.find('[data-format]').on('click',function(){const key=$(this).data('format');b[key]=!b[key];self.render_page();self.select(b.id);self.mark_dirty()});
    box.find('.wds-delete').on('click',()=>this.delete_selected());
  }

  prop(key,label,val,type,step){return `<div class="wds-prop"><label>${label}</label>${type==='textarea'?`<textarea data-key="${key}">${frappe.utils.escape_html(String(val))}</textarea>`:`<input type="${type}" ${step?`step="${step}"`:''} data-key="${key}" value="${frappe.utils.escape_html(String(val))}">`}</div>`}
  select_prop(key,label,val,options){return `<div class="wds-prop"><label>${label}</label><select data-key="${key}">${options.map(x=>`<option value="${x}" ${x===val?'selected':''}>${__(x)}</option>`).join('')}</select></div>`}

  render_fields(){
    const fields=this.template.meta_fields||[];
    const groups={General:[],Data:[],Date:[],Financial:[],Links:[]};
    fields.forEach(f=>{const t=f.fieldtype||'';if(['Currency','Float','Int','Percent'].includes(t))groups.Financial.push(f);else if(['Date','Datetime','Time'].includes(t))groups.Date.push(f);else if(['Link','Dynamic Link'].includes(t))groups.Links.push(f);else if(['Data','Text','Small Text','Long Text','Select','Check'].includes(t))groups.Data.push(f);else groups.General.push(f)});
    const box=this.wrapper.find('.wds-fields').empty();
    Object.entries(groups).forEach(([name,rows])=>{if(!rows.length)return;box.append(`<details open><summary>${__(name)} <span>${rows.length}</span></summary><div>${rows.map(f=>`<button class="wds-field-chip" data-search="${frappe.utils.escape_html((f.label||f.fieldname)+' '+f.fieldname)}" data-field="${frappe.utils.escape_html(f.fieldname)}"><b>${frappe.utils.escape_html(f.label||f.fieldname)}</b><small>${frappe.utils.escape_html(f.fieldname)}</small></button>`).join('')}</div></details>`)});
  }
  filter_fields(q){q=(q||'').toLowerCase();this.wrapper.find('.wds-field-chip').each(function(){$(this).toggle(($(this).data('search')||'').toLowerCase().includes(q))})}

  render_page_properties(){const t=this.template;this.wrapper.find('.wds-page-properties').html(`${this.select_prop('page_size',__('Page Size'),t.page_size,['A4','A5','Letter'])}${this.select_prop('orientation',__('Orientation'),t.orientation,['Portrait','Landscape'])}${this.select_prop('direction',__('Direction'),t.direction,['RTL','LTR'])}<div class="wds-prop-row">${this.prop('margin_top_mm',__('Top Margin'),t.margin_top_mm,'number')}${this.prop('margin_right_mm',__('Right Margin'),t.margin_right_mm,'number')}</div><div class="wds-prop-row">${this.prop('margin_bottom_mm',__('Bottom Margin'),t.margin_bottom_mm,'number')}${this.prop('margin_left_mm',__('Left Margin'),t.margin_left_mm,'number')}</div>`)}
  update_page(){const self=this;this.wrapper.find('.wds-page-properties input,.wds-page-properties select').each(function(){const k=$(this).data('key');if(k)self.template[k]=$(this).attr('type')==='number'?Number(this.value):this.value});this.render_page();this.mark_dirty()}

  copy_selected(){if(this.selected)this.clipboard=JSON.parse(JSON.stringify(this.get(this.selected)))}
  paste_selected(){if(!this.clipboard)return;const b=JSON.parse(JSON.stringify(this.clipboard));b.id='b'+Date.now()+Math.floor(Math.random()*1000);b.x+=20;b.y+=20;b.z=this.max_z()+1;this.blocks.push(b);this.render_page();this.select(b.id);this.mark_dirty()}
  duplicate_selected(){this.copy_selected();this.paste_selected()}
  delete_selected(){if(!this.selected)return;this.blocks=this.blocks.filter(x=>x.id!==this.selected);this.selected=null;this.render_page();this.render_properties();this.mark_dirty()}
  layer(delta){const b=this.get(this.selected);if(!b)return;b.z=Math.max(1,Number(b.z||1)+delta);this.render_page();this.select(b.id);this.mark_dirty()}
  toggle_lock(){const b=this.get(this.selected);if(!b)return;b.locked=!b.locked;this.render_page();this.select(b.id);this.mark_dirty()}

  async new_template(){const d=new frappe.ui.Dialog({title:__('New Template'),fields:[{fieldname:'template_title',fieldtype:'Data',label:__('Template Title'),reqd:1},{fieldname:'reference_doctype',fieldtype:'Link',options:'DocType',label:__('Reference DocType'),reqd:1},{fieldname:'document_category',fieldtype:'Select',options:'Hotel Undertaking\nContract\nQuotation\nInvoice\nOperation Order\nProduction Order\nPreparation Order\nLoading Order\nDelivery Note\nCertificate\nReport\nOther',label:__('Category'),default:'Other'}],primary_action_label:__('Create'),primary_action:async v=>{const r=await frappe.call('wafd_one.document_studio.create_template',v);d.hide();await this.load_templates();this.wrapper.find('.wds-template').val(r.message);this.load_template(r.message)}});d.show()}
  async save(){if(!this.template)return;const args={template_name:this.template.name,canvas_json:JSON.stringify({version:2,blocks:this.blocks}),page_settings:JSON.stringify(this.template)};await frappe.call({method:'wafd_one.document_studio.save_template',args,freeze:true,freeze_message:__('Saving template...')});this.dirty=false;this.status(__('Saved'));frappe.show_alert({message:__('Template saved'),indicator:'green'})}
  preview(){if(!this.template)return;window.open(`/api/method/wafd_one.document_studio.preview_html?template_name=${encodeURIComponent(this.template.name)}`,'_blank')}
  pdf(){if(!this.template)return;window.open(`/api/method/wafd_one.document_studio.download_pdf?template_name=${encodeURIComponent(this.template.name)}`,'_blank')}
  mark_dirty(){this.dirty=true;this.status(__('Unsaved changes'))}
  status(s){this.wrapper.find('.wds-status').text(s)}
}
