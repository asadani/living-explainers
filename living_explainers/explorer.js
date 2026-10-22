(() => {
  'use strict';
  const payload = JSON.parse(document.getElementById('model-data').textContent);
  const {model, freshness} = payload;
  const pathSelect = document.getElementById('path-select');
  const questionSelect = document.getElementById('question-select');
  const stepsEl = document.getElementById('steps');
  const detailTitle = document.getElementById('detail-title');
  const detailBody = document.getElementById('detail-body');
  const notCovered = document.getElementById('not-covered');
  const focusReview = document.getElementById('focus-review');
  const statuses = new Map(freshness.sources.map(item => [item.id, item]));
  const nodes = new Map(model.nodes.map(item => [item.id, item]));
  const put = (node, value) => { node.textContent = value; };
  const addOption = (select, value, label) => { const option=document.createElement('option'); option.value=value; option.textContent=label; select.append(option); };
  model.paths.forEach(path => addOption(pathSelect, path.id, path.label));
  addOption(questionSelect, '', 'Choose a question…');
  model.questions.forEach(question => addOption(questionSelect, question.id, question.label));
  const render = () => {
    const path = model.paths.find(item => item.id === pathSelect.value) || model.paths[0];
    const question = model.questions.find(item => item.id === questionSelect.value);
    if (question && !question.path_id) {
      stepsEl.replaceChildren(); notCovered.hidden=false; put(notCovered, question.note); detailTitle.textContent='Not covered'; detailBody.textContent='This question has no authored path. No behavior has been inferred.'; return;
    }
    notCovered.hidden=true;
    const activePath = question && question.path_id ? model.paths.find(item => item.id === question.path_id) : path;
    if (activePath && activePath.id !== pathSelect.value) pathSelect.value=activePath.id;
    put(document.getElementById('path-meta'), `${activePath.steps.length} authored steps · ${activePath.origin}`);
    const rows = activePath.steps.map((step,index) => {
      const node=nodes.get(step.node_id);
      const refs=node.source_ids.map(id => statuses.get(id));
      const needsReview=node.origin==='proposed' || refs.some(ref => !ref || ref.status!=='current');
      const li=document.createElement('li'); li.className='step';
      if (focusReview.checked && !needsReview && !(node.assumptions||[]).length) li.classList.add('deemphasized');
      const button=document.createElement('button'); button.type='button'; button.setAttribute('aria-current',String(index===0));
      const number=document.createElement('span'); number.className='step-number'; number.textContent=String(index+1).padStart(2,'0');
      const copy=document.createElement('span'); const name=document.createElement('span'); name.className='step-name'; name.textContent=node.label;
      const summary=document.createElement('span'); summary.className='step-summary'; summary.textContent=node.summary; copy.append(name,summary);
      const tag=document.createElement('span'); tag.className=`tag${needsReview?' review':''}`; tag.textContent=needsReview?'Review needed':node.origin; button.append(number,copy,tag);
      button.addEventListener('click', () => { stepsEl.querySelectorAll('button').forEach(b=>b.setAttribute('aria-current','false')); button.setAttribute('aria-current','true'); showStep(step,node,activePath); });
      li.append(button); return {li,step,node};
    });
    stepsEl.replaceChildren(...rows.map(x=>x.li));
    if(rows.length) showStep(rows[0].step,rows[0].node,activePath);
  };
  function showStep(step,node,path) {
    detailTitle.textContent=node.label;
    detailBody.replaceChildren();
    const explanation=document.createElement('p'); explanation.textContent=step.explanation; detailBody.append(explanation);
    const summary=document.createElement('p'); summary.className='small'; summary.textContent=`${node.origin} · ${node.summary}`; detailBody.append(summary);
    if(node.assumptions && node.assumptions.length){const head=document.createElement('p');head.className='eyebrow';head.textContent='ASSUMPTIONS';detailBody.append(head);for(const item of node.assumptions){const p=document.createElement('p');p.textContent=item;detailBody.append(p);}}
    const heading=document.createElement('p');heading.className='eyebrow';heading.textContent='SOURCE REFERENCES';detailBody.append(heading);
    if(!node.source_ids.length){const p=document.createElement('p');p.className='small';p.textContent='No source attached to this proposed step.';detailBody.append(p);}
    const list=document.createElement('ul');list.className='source-list';
    for(const id of node.source_ids){const ref=model.sources.find(x=>x.id===id);const status=statuses.get(id);const li=document.createElement('li');li.textContent=`${ref.path}:${ref.line_start}–${ref.line_end}`;const state=document.createElement('span');state.className='source-status';state.textContent=`${status?status.status:'missing'}${status && status.range_valid===false?' · cited range no longer exists':''}`;li.append(state);list.append(li);}
    detailBody.append(list);
    const outcome=document.createElement('p');outcome.className='small';outcome.textContent=`Path outcome: ${path.outcome}`;detailBody.append(outcome);
  }
  pathSelect.addEventListener('change',()=>{questionSelect.value='';render();});
  questionSelect.addEventListener('change',render);
  focusReview.addEventListener('change',render);
  render();
})();
