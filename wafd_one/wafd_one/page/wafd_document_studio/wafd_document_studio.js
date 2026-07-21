
frappe.pages['wafd-document-studio'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({parent: wrapper, title: __('WAFD Document Studio'), single_column: true});
  new WAFDDocumentStudio(page, wrapper);
};

class WAFDDocumentStudio {
  constructor(page, wrapper) {
    this.page=page; this.wrapper=$(wrapper); this.template=null; this.blocks=[]; this.selected=null; this.dirty=false;
    this.render(); this.bind(); this.load_templates();
  }
  render(){
    $(frappe.render_template ? '<div></div>' : '<div></div>');
    this.wrapper.find('.layout-main-section').html(`
      <div class="wds-topbar">
        <select class="form-control wds-template" style="max-width:320px"></select>
        <button class="btn btn-default btn-sm wds-new">${__('New Template')}</button>
        <button class="btn btn-primary btn-sm wds-save">${__('Save')}</button>
        <button class="btn btn-default btn-sm wds-preview">${__('Preview')}</button>
        <button class="btn btn-default btn-sm wds-pdf">${__('PDF')}</button>
        <span class="wds-status"></span>
      </div>
      <div class="wds-shell">
        <div class="wds-panel"><h4>${__('Elements')}</h4>
          ${this.tool('text',__('Text'))}${this.tool('field',__('Dynamic Field'))}${this.tool('image',__('Image'))}${this.tool('logo',__('Logo'))}${this.tool('stamp',__('Stamp'))}${this.tool('signature',__('Signature'))}${this.tool('line',__('Line'))}${this.tool('table',__('Table'))}${this.tool('qr',__('QR Placeholder'))}
          <hr><h4>${__('Document Fields')}</h4><div class="wds-fields"><div class="wds-empty">${__('Select a template')}</div></div>
        </div>
        <div class="wds-panel wds-stage-wrap"><div class="wds-page"></div></div>
        <div class="wds-panel"><h4>${__('Properties')}</h4><div class="wds-properties"><div class="wds-empty">${__('Select an element')}</div></div><hr><h4>${__('Page')}</h4><div class="wds-page-properties"></div></div>
      </div>`);
  }
  tool(type,label){return `<button class="btn btn-default btn-sm wds-tool" data-type="${type}">+ ${label}</button>`}
  bind(){
    this.wrapper.on('click','.wds-tool',e=>this.add_block($(e.currentTarget).data('type')));
    this.wrapper.on('click','.wds-new',()=>this.new_template());
    this.wrapper.on('click','.wds-save',()=>this.save());
    this.wrapper.on('click','.wds-preview',()=>this.preview());
    this.wrapper.on('click','.wds-pdf',()=>this.pdf());
    this.wrapper.on('change','.wds-template',e=>this.load_template(e.target.value));
    this.wrapper.on('click','.wds-field-chip',e=>this.add_field($(e.currentTarget).data('field')));
    this.wrapper.on('input change','.wds-page-properties input,.wds-page-properties select',()=>this.update_page());
    this.wrapper.on('click','.wds-page',e=>{if(e.target===e.currentTarget)this.select(null)});
    window.addEventListener('beforeunload',e=>{if(this.dirty){e.preventDefault();e.returnValue='';}});
  }
  async load_templates(){const r=await frappe.call('wafd_one.document_studio.list_templates'); const rows=r.message||[]; const sel=this.wrapper.find('.wds-template').empty().append(`<option value="">${__('Select Template')}</option>`); rows.forEach(x=>sel.append(`<option value="${frappe.utils.escape_html(x.name)}">${frappe.utils.escape_html(x.template_title)} — ${frappe.utils.escape_html(x.reference_doctype)}</option>`)); const route=frappe.route_options||{}; frappe.route_options=null; if(route.template){sel.val(route.template); this.load_template(route.template);}}
  async load_template(name){if(!name)return; const r=await frappe.call('wafd_one.document_studio.get_template',{template_name:name}); this.template=r.message; this.blocks=(this.template.canvas&&this.template.canvas.blocks)||[]; this.render_page(); this.render_fields(); this.render_page_properties(); this.dirty=false; this.status(__('Loaded'))}
  render_page(){const t=this.template||{}; const landscape=t.orientation==='Landscape'; const mm=landscape?[297,210]:[210,297]; const page=this.wrapper.find('.wds-page').css({width:`${mm[0]*3.78}px`,height:`${mm[1]*3.78}px`,direction:(t.direction||'RTL').toLowerCase()}).empty(); this.blocks.forEach(b=>page.append(this.block_html(b))); this.bind_blocks();}
  block_html(b){const style=`left:${b.x}px;top:${b.y}px;width:${b.w}px;height:${b.h}px;z-index:${b.z||1};${b.style||''}`; let content=''; if(['image','logo','stamp','signature'].includes(b.type)){content=b.src?`<img src="${frappe.utils.escape_html(b.src)}" style="width:100%;height:100%;object-fit:contain">`:`<div class="wds-empty">${__(b.type)}</div>`;} else if(b.type==='line'){content='<div style="border-top:1px solid #222;margin-top:50%"></div>';} else if(b.type==='table'){content='<table style="width:100%;border-collapse:collapse"><tr><th style="border:1px solid #333">{{ _(\"Item\") }}</th><th style="border:1px solid #333">{{ _(\"Value\") }}</th></tr><tr><td style="border:1px solid #333">...</td><td style="border:1px solid #333">...</td></tr></table>';} else if(b.type==='qr'){content='<div style="border:1px solid #333;width:100%;height:100%;display:flex;align-items:center;justify-content:center">QR</div>';} else {content=b.html||__('Double click to edit');}
    const editable=['text','field','table'].includes(b.type)?'contenteditable="true"':''; return `<div class="wds-block" data-id="${b.id}" style="${style}"><div class="wds-content" ${editable}>${content}</div><span class="wds-resizer"></span></div>`;}
  bind_blocks(){const self=this; this.wrapper.find('.wds-block').each(function(){const el=this,id=$(this).data('id'); el.addEventListener('pointerdown',e=>{if($(e.target).hasClass('wds-resizer'))return; self.select(id); const b=self.get(id),sx=e.clientX,sy=e.clientY,ox=b.x,oy=b.y; el.setPointerCapture(e.pointerId); const move=ev=>{b.x=Math.max(0,ox+ev.clientX-sx);b.y=Math.max(0,oy+ev.clientY-sy);el.style.left=b.x+'px';el.style.top=b.y+'px';self.mark_dirty()}; const up=()=>{el.removeEventListener('pointermove',move);el.removeEventListener('pointerup',up)};el.addEventListener('pointermove',move);el.addEventListener('pointerup',up)}); $(this).find('.wds-resizer')[0].addEventListener('pointerdown',e=>{e.stopPropagation();self.select(id);const b=self.get(id),sx=e.clientX,sy=e.clientY,ow=b.w,oh=b.h;e.target.setPointerCapture(e.pointerId);const move=ev=>{b.w=Math.max(25,ow+ev.clientX-sx);b.h=Math.max(20,oh+ev.clientY-sy);el.style.width=b.w+'px';el.style.height=b.h+'px';self.mark_dirty()};const up=()=>{e.target.removeEventListener('pointermove',move);e.target.removeEventListener('pointerup',up)};e.target.addEventListener('pointermove',move);e.target.addEventListener('pointerup',up)}); $(this).find('.wds-content').on('input',function(){const b=self.get(id);b.html=this.innerHTML;self.mark_dirty()});});}
  add_block(type){if(!this.template)return frappe.msgprint(__('Select or create a template first.')); const id='b'+Date.now(); const map={text:{w:300,h:60,html:__('Editable text')},field:{w:260,h:40,html:'{{ doc.name }}'},image:{w:150,h:100},logo:{w:180,h:90,src:this.template.logo},stamp:{w:130,h:130,src:this.template.stamp},signature:{w:160,h:80,src:this.template.signature},line:{w:400,h:20},table:{w:450,h:100},qr:{w:100,h:100}}; this.blocks.push({id,type,x:40,y:40,w:map[type].w,h:map[type].h,html:map[type].html||'',src:map[type].src||'',z:this.blocks.length+1,style:''}); this.render_page();this.select(id);this.mark_dirty();}
  add_field(field){this.add_block('field'); const b=this.blocks[this.blocks.length-1];b.html=`{{ doc.get("${field}") or "" }}`;this.render_page();this.select(b.id)}
  select(id){this.selected=id;this.wrapper.find('.wds-block').removeClass('selected');if(id)this.wrapper.find(`.wds-block[data-id="${id}"]`).addClass('selected');this.render_properties()}
  get(id){return this.blocks.find(x=>x.id===id)}
  render_properties(){const box=this.wrapper.find('.wds-properties');if(!this.selected)return box.html(`<div class="wds-empty">${__('Select an element')}</div>`);const b=this.get(this.selected);box.html(`${this.prop('x','X',b.x,'number')}${this.prop('y','Y',b.y,'number')}${this.prop('w',__('Width'),b.w,'number')}${this.prop('h',__('Height'),b.h,'number')}${this.prop('z',__('Layer'),b.z,'number')}${this.prop('style',__('CSS Style'),b.style||'','textarea')}${['image','logo','stamp','signature'].includes(b.type)?this.prop('src',__('Image URL'),b.src||'','text'):''}<button class="btn btn-danger btn-sm wds-delete">${__('Delete')}</button>`);const self=this;box.find('input,textarea').on('input change',function(){b[$(this).data('key')]=$(this).attr('type')==='number'?Number(this.value):this.value;self.render_page();self.select(b.id);self.mark_dirty()});box.find('.wds-delete').on('click',()=>{this.blocks=this.blocks.filter(x=>x.id!==b.id);this.selected=null;this.render_page();this.render_properties();this.mark_dirty()});}
  prop(key,label,val,type){return `<div class="wds-prop"><label>${label}</label>${type==='textarea'?`<textarea data-key="${key}">${frappe.utils.escape_html(String(val))}</textarea>`:`<input type="${type}" data-key="${key}" value="${frappe.utils.escape_html(String(val))}">`}</div>`}
  select_prop(key,label,val,options){return `<div class="wds-prop"><label>${label}</label><select data-key="${key}">${options.map(x=>`<option value="${x}" ${x===val?'selected':''}>${__(x)}</option>`).join('')}</select></div>`}
  render_fields(){const box=this.wrapper.find('.wds-fields').html('');(this.template.meta_fields||[]).forEach(f=>box.append(`<span class="wds-field-chip" data-field="${f.fieldname}" title="${frappe.utils.escape_html(f.fieldtype)}">${frappe.utils.escape_html(f.label||f.fieldname)}</span>`))}
  render_page_properties(){const t=this.template;this.wrapper.find('.wds-page-properties').html(`${this.select_prop('page_size',__('Page Size'),t.page_size,['A4','A5','Letter'])}${this.select_prop('orientation',__('Orientation'),t.orientation,['Portrait','Landscape'])}${this.select_prop('direction',__('Direction'),t.direction,['RTL','LTR'])}${this.prop('margin_top_mm',__('Top Margin'),t.margin_top_mm,'number')}${this.prop('margin_right_mm',__('Right Margin'),t.margin_right_mm,'number')}${this.prop('margin_bottom_mm',__('Bottom Margin'),t.margin_bottom_mm,'number')}${this.prop('margin_left_mm',__('Left Margin'),t.margin_left_mm,'number')}`)}
  update_page(){const self=this;this.wrapper.find('.wds-page-properties input,.wds-page-properties select').each(function(){const k=$(this).data('key');if(k)self.template[k]=$(this).attr('type')==='number'?Number(this.value):this.value});this.render_page();this.mark_dirty()}
  async new_template(){const d=new frappe.ui.Dialog({title:__('New Template'),fields:[{fieldname:'template_title',fieldtype:'Data',label:__('Template Title'),reqd:1},{fieldname:'reference_doctype',fieldtype:'Link',options:'DocType',label:__('Reference DocType'),reqd:1},{fieldname:'document_category',fieldtype:'Select',options:'Hotel Undertaking\nContract\nQuotation\nInvoice\nOperation Order\nProduction Order\nPreparation Order\nLoading Order\nDelivery Note\nCertificate\nReport\nOther',label:__('Category'),default:'Other'}],primary_action_label:__('Create'),primary_action:async v=>{const r=await frappe.call('wafd_one.document_studio.create_template',v);d.hide();await this.load_templates();this.wrapper.find('.wds-template').val(r.message);this.load_template(r.message)}});d.show()}
  async save(){if(!this.template)return; const args={template_name:this.template.name,canvas_json:JSON.stringify({version:1,blocks:this.blocks}),page_settings:JSON.stringify(this.template)};await frappe.call({method:'wafd_one.document_studio.save_template',args,freeze:true,freeze_message:__('Saving template...')});this.dirty=false;this.status(__('Saved'));frappe.show_alert({message:__('Template saved'),indicator:'green'})}
  preview(){if(!this.template)return;window.open(`/api/method/wafd_one.document_studio.preview_html?template_name=${encodeURIComponent(this.template.name)}`,'_blank')}
  pdf(){if(!this.template)return;window.open(`/api/method/wafd_one.document_studio.download_pdf?template_name=${encodeURIComponent(this.template.name)}`,'_blank')}
  mark_dirty(){this.dirty=true;this.status(__('Unsaved changes'))}
  status(s){this.wrapper.find('.wds-status').text(s)}
}
