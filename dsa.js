(() => {
  const sortBars=document.getElementById("merge-bars");
  const sortStatus=document.getElementById("merge-status");
  const sortPlay=document.getElementById("sort-play");
  const sortNext=document.getElementById("sort-next");
  const sortReset=document.getElementById("sort-reset");
  const initialValues=[8,3,6,1,7,4];
  const sortFrames=[];
  const work=initialValues.slice();
  const sortItems=initialValues.map((value,index)=>{
    const item=document.createElement("div");
    item.className="dsa-bar";
    item.setAttribute("role","listitem");
    const number=document.createElement("span");number.textContent=String(value);item.append(number);
    sortBars.append(item);return item;
  });

  function mergeRange(first,last) {
    if(last-first<=1) return work.slice(first,last);
    const middle=Math.floor((first+last)/2);
    sortFrames.push({values:work.slice(),first,last:last-1,label:`Split positions ${first+1}–${last} into two ranges.`});
    const left=mergeRange(first,middle);
    const right=mergeRange(middle,last);
    const merged=[];
    let i=0,j=0;
    while(i<left.length&&j<right.length) merged.push(left[i]<=right[j]?left[i++]:right[j++]);
    while(i<left.length) merged.push(left[i++]);
    while(j<right.length) merged.push(right[j++]);
    work.splice(first,merged.length,...merged);
    sortFrames.push({values:work.slice(),first,last:last-1,label:`Merge positions ${first+1}–${last}: ${merged.join(", ")}.`});
    return merged;
  }
  mergeRange(0,work.length);
  let sortIndex=-1,sortTimer=null;

  function drawSort() {
    const frame=sortIndex<0?{values:initialValues,first:-1,last:-1,label:"Ready to sort."}:sortFrames[sortIndex];
    const max=Math.max(...initialValues);
    frame.values.forEach((value,index)=>{
      const item=sortItems[index];
      item.className="dsa-bar"+(index>=frame.first&&index<=frame.last?" is-active":"");
      item.setAttribute("aria-label",`Value ${value}, position ${index+1}`);
      item.style.setProperty("--bar-height",`${28+value/max*72}%`);
      item.firstElementChild.textContent=String(value);
    });
    sortStatus.textContent=sortIndex<0?"Ready to sort.":`Step ${sortIndex+1} of ${sortFrames.length}: ${frame.label}`;
  }
  function stepSort() { if(sortIndex<sortFrames.length-1){sortIndex++;drawSort();}else stopSort(); }
  function stopSort(){if(sortTimer){clearInterval(sortTimer);sortTimer=null;}sortPlay.textContent="Play";}
  sortNext.addEventListener("click",stepSort);
  sortReset.addEventListener("click",()=>{stopSort();sortIndex=-1;drawSort();});
  sortPlay.addEventListener("click",()=>{
    if(sortTimer){stopSort();return;}
    if(sortIndex>=sortFrames.length-1)sortIndex=-1;
    sortPlay.textContent="Pause";
    drawSort();
    const delay=window.matchMedia("(prefers-reduced-motion: reduce)").matches?100:650;
    sortTimer=setInterval(()=>{if(sortIndex>=sortFrames.length-1){stopSort();return;}stepSort();},delay);
  });
  drawSort();

  const items=[
    {id:"IS000014",name:"Pothole · Kothrud",priority:8.6},
    {id:"IS000021",name:"Blocked drain · Baner",priority:9.2},
    {id:"IS000008",name:"Streetlight · Aundh",priority:6.1},
    {id:"IS000017",name:"Broken footpath · Deccan",priority:7.4},
  ];
  const heapFrames=[];
  const heap=[];
  const removed=[];
  const higher=(a,b)=>a.priority===b.priority?a.id<b.id:a.priority>b.priority;
  for(const item of items){
    heap.push(item);let index=heap.length-1;
    while(index>0){const parent=Math.floor((index-1)/2);if(!higher(heap[index],heap[parent]))break;[heap[index],heap[parent]]=[heap[parent],heap[index]];index=parent;}
    heapFrames.push({heap:heap.slice(),removed:removed.slice(),label:`Insert ${item.name} (${item.priority}).`});
  }
  while(heap.length){
    const top=heap[0];const last=heap.pop();
    if(heap.length){heap[0]=last;let index=0;while(true){const left=index*2+1,right=left+1;let best=index;if(left<heap.length&&higher(heap[left],heap[best]))best=left;if(right<heap.length&&higher(heap[right],heap[best]))best=right;if(best===index)break;[heap[index],heap[best]]=[heap[best],heap[index]];index=best;}}
    removed.push(top);
    heapFrames.push({heap:heap.slice(),removed:removed.slice(),label:`Remove highest: ${top.name} (${top.priority}).`});
  }
  const heapArray=document.getElementById("heap-array");
  const heapStatus=document.getElementById("heap-status");
  const heapOutput=document.getElementById("heap-output");
  const heapPlay=document.getElementById("heap-play");
  const heapNext=document.getElementById("heap-next");
  const heapReset=document.getElementById("heap-reset");
  let heapIndex=-1,heapTimer=null;
  function drawHeap(){
    const frame=heapIndex<0?{heap:[],removed:[],label:"Ready to build the heap."}:heapFrames[heapIndex];
    heapArray.replaceChildren(...frame.heap.map((item,index)=>{
      const node=document.createElement("div");node.className="heap-node"+(index===0?" heap-root":"");node.setAttribute("role","listitem");
      const ref=document.createElement("b");ref.textContent=item.id;
      const label=document.createElement("span");label.textContent=item.name;
      const score=document.createElement("strong");score.textContent=`Priority ${item.priority.toFixed(1)}`;
      node.append(ref,label,score);return node;
    }));
    heapOutput.replaceChildren(...frame.removed.map(item=>{const li=document.createElement("li");li.textContent=`${item.name} · ${item.priority.toFixed(1)}`;return li;}));
    heapStatus.textContent=heapIndex<0?"Ready to build the heap.":`Step ${heapIndex+1} of ${heapFrames.length}: ${frame.label}`;
  }
  function stopHeap(){if(heapTimer){clearInterval(heapTimer);heapTimer=null;}heapPlay.textContent="Play";}
  function stepHeap(){if(heapIndex<heapFrames.length-1){heapIndex++;drawHeap();}else stopHeap();}
  heapNext.addEventListener("click",stepHeap);
  heapReset.addEventListener("click",()=>{stopHeap();heapIndex=-1;drawHeap();});
  heapPlay.addEventListener("click",()=>{
    if(heapTimer){stopHeap();return;}
    if(heapIndex>=heapFrames.length-1)heapIndex=-1;
    heapPlay.textContent="Pause";drawHeap();
    const delay=window.matchMedia("(prefers-reduced-motion: reduce)").matches?100:650;
    heapTimer=setInterval(()=>{if(heapIndex>=heapFrames.length-1){stopHeap();return;}stepHeap();},delay);
  });
  drawHeap();
})();
