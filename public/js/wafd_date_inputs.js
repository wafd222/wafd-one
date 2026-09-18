(function(){
  "use strict";
  const selector="input[type='date']:not([data-wafd-date-ready])";
  function formatted(value){
    const match=String(value||"").match(/^(\d{4})-(\d{2})-(\d{2})$/);
    return match?`${match[3]}-${match[2]}-${match[1]}`:"DD-MM-YYYY";
  }
  function sync(input){
    const shell=input.closest(".wafd-date-shell"),display=shell&&shell.querySelector(".wafd-date-display");
    if(display){display.textContent=formatted(input.value);display.classList.toggle("is-empty",!input.value)}
  }
  function enhance(root=document){
    root.querySelectorAll?.(selector).forEach(input=>{
      input.dataset.wafdDateReady="1";
      const shell=document.createElement("span"),display=document.createElement("span");
      shell.className="wafd-date-shell";display.className="wafd-date-display";display.setAttribute("dir","ltr");
      input.parentNode.insertBefore(shell,input);shell.appendChild(input);shell.appendChild(display);
      input.addEventListener("input",()=>sync(input));input.addEventListener("change",()=>sync(input));input.addEventListener("blur",()=>sync(input));sync(input);
    });
  }
  function start(){enhance();new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(node=>{if(node.nodeType===1){if(node.matches?.(selector))enhance(node.parentNode);else enhance(node)}}))).observe(document.body,{childList:true,subtree:true});setInterval(()=>document.querySelectorAll("input[data-wafd-date-ready]").forEach(sync),750)}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();
