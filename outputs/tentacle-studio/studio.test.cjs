const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const source = fs.readFileSync(__dirname + '/studio.js', 'utf8');
const prefix = source.slice(0, source.indexOf('  const overview='));
const cycleStart = source.indexOf('  function hasCycle(');
const cycleEnd = source.indexOf('  function check()', cycleStart);
const context = {localStorage: {getItem: () => null}};
const api = vm.runInNewContext(prefix + source.slice(cycleStart, cycleEnd) +
  'return {initial,validImport,esc,inspectFlow,roles,panels,cycle: edges=>hasCycle(edges)};})();', context);

test('professional roles expose complete operating contracts', () => {
  assert.ok(api.roles.length >= 8);
  for (const role of api.roles) {
    for (const key of ['name', 'level', 'method', 'output', 'boundary', 'cap']) {
      assert.equal(typeof role[key], 'string');
      assert.ok(role[key].trim(), `${role.type}.${key}`);
    }
  }
});

test('framework visualization includes long-run supervision', () => {
  assert.ok(api.panels.length >= 12);
  assert.ok(api.panels.some(panel => panel.id === 'autonomy'));
});

test('all templates have valid bounded structure', () => {
  for (const kind of ['research', 'code', 'media']) {
    assert.equal(api.validImport(api.initial(kind)), true);
  }
});
test('dependency cycle including self-loop is rejected', () => {
  const edges = api.initial().edges;
  assert.equal(api.cycle(edges), false);
  assert.equal(api.cycle([...edges, ['n6','n1']]), true);
  assert.equal(api.cycle([...edges, ['n2','n2']]), true);
});
test('unknown edge targets and duplicate identities are rejected', () => {
  let flow = api.initial();
  flow.edges.push(['n1', 'unknown']);
  assert.equal(api.validImport(flow), false);
  flow = api.initial();
  flow.nodes[1].id = flow.nodes[0].id;
  assert.equal(api.validImport(flow), false);
});
test('malformed imports and runtime budgets fail closed', () => {
  for (const value of [null, {}, [], 'text']) assert.ok(!api.validImport(value));
  const broken = api.initial();
  broken.nodes[0] = null;
  assert.equal(api.validImport(broken), false);
  for (const [key,value] of [['timeout',0],['timeout',3601],['retries',6],['x',Infinity],['type','shell'],['id','<script>']]) {
    const flow = api.initial();
    flow.nodes[0][key] = value;
    assert.equal(api.validImport(flow), false);
  }
});
test('untrusted labels are escaped before HTML rendering', () => {
  assert.equal(api.esc('<img src=x onerror="bad">'), '&lt;img src=x onerror=&quot;bad&quot;&gt;');
});
test('approval cannot bypass review and delivery cannot bypass approval', () => {
  const flow = api.initial();
  flow.nodes.forEach(item => item.prompt = 'Defined task');
  assert.equal(api.inspectFlow(flow).length, 0);
  flow.edges.push(['n1', 'n5']);
  assert.ok(api.inspectFlow(flow).includes('主人审批必须直接依赖独立复核'));
  flow.edges.push(['n1', 'n6']);
  assert.ok(api.inspectFlow(flow).includes('交付必须直接依赖主人审批'));
});
