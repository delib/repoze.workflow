import unittest
from repoze.bfg import testing

class TestWorkflowDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import WorkflowDirective
        return WorkflowDirective

    def _makeOne(self, context=None, name=None, initial_state=None,
                 state_attr=None, class_=None):
        if context is None:
            context = DummyContext()
        return self._getTargetClass()(context, name, initial_state,
                                      state_attr, class_)

    def test_ctor_with_state_attr(self):
        ctor = self._makeOne(name='public', state_attr='public2')
        self.assertEqual(ctor.state_attr, 'public2')
        
    def test_ctor_no_state_attr(self):
        ctor = self._makeOne(name='public')
        self.assertEqual(ctor.state_attr, 'public')

    def test_ctor_with_class_(self):
        ctor = self._makeOne(name='public', class_='class')
        self.assertEqual(ctor.class_, 'class')
        
    def test_ctor_no_class_(self):
        from repoze.bfg.workflow.workflow import Workflow
        ctor = self._makeOne(name='public')
        self.assertEqual(ctor.class_, Workflow)

    def test_after(self):
        from repoze.bfg.workflow.zcml import handler
        from repoze.bfg.workflow.interfaces import IWorkflow
        from repoze.bfg.workflow.workflow import Workflow
        directive = self._makeOne(initial_state='public')
        directive.states = [ DummyState('s1', a=1), DummyState('s2', b=2) ]
        directive.transitions = [ DummyTransition('make_public'),
                                  DummyTransition('make_private'),
                                  ]
        directive.after()
        actions = directive.context.actions
        self.assertEqual(len(actions), 1)
        action = actions[0]
        self.assertEqual(action[0], (IWorkflow, None))
        self.assertEqual(action[1], handler)
        self.assertEqual(action[2][0], 'registerUtility')
        utility = action[2][1]
        self.assertEqual(type(utility), Workflow)
        self.assertEqual(action[2][2], IWorkflow)
        self.assertEqual(action[2][3], None)
        self.assertEqual(action[2][4], None)
        self.assertEqual(utility.__class__, Workflow)
        self.assertEqual(
            utility._transition_data,
            [{'from_state': 'private', 'callback': None,
              'name': 'make_public', 'to_state': 'public'},
             {'from_state': 'private', 'callback': None,
              'name': 'make_private', 'to_state': 'public'}]
            )
        self.assertEqual(utility.initial_state, 'public')
        

class TestTransitionDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import TransitionDirective
        return TransitionDirective

    def _makeOne(self, context=None, name=None, callback=None, from_state=None,
                 to_state=None, permission=None):
        return self._getTargetClass()(context, name, callback, from_state,
                                      to_state, permission)

    def test_ctor(self):
        directive = self._makeOne('context', 'name', 'callback', 'from_state',
                                  'to_state', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, 'from_state')
        self.assertEqual(directive.to_state, 'to_state')
        self.assertEqual(directive.permission, 'permission')
        self.assertEqual(directive.extras, {})

    def test_ctor_no_from_state(self):
        directive = self._makeOne('context', 'name', 'callback', '',
                                  'to_state', 'permission')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')
        self.assertEqual(directive.callback, 'callback')
        self.assertEqual(directive.from_state, None)
        self.assertEqual(directive.to_state, 'to_state')
        self.assertEqual(directive.permission, 'permission')
        self.assertEqual(directive.extras, {})

    def test_after(self):
        context = DummyContext(transitions=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.transitions, [directive])

class TestStateDirective(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from repoze.bfg.workflow.zcml import StateDirective
        return StateDirective

    def _makeOne(self, context=None, name=None):
        return self._getTargetClass()(context, name)

    def test_ctor(self):
        directive = self._makeOne('context', 'name')
        self.assertEqual(directive.context, 'context')
        self.assertEqual(directive.name, 'name')

    def test_after(self):
        context = DummyContext(states=[])
        directive = self._makeOne(context)
        directive.after()
        self.assertEqual(context.states, [directive])

class TestKeyValuePair(unittest.TestCase):
    def _callFUT(self, context, key, value):
        from repoze.bfg.workflow.zcml import key_value_pair
        key_value_pair(context, key, value)

    def test_it_no_extras(self):
        context = DummyContext()
        context.context = DummyContext()
        self._callFUT(context, 'key', 'value')
        self.assertEqual(context.context.extras, {'key':'value'})

class TestFixtureApp(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def test_execute_actions(self):
        from repoze.bfg.workflow.interfaces import IWorkflow
        from repoze.bfg.workflow.workflow import Workflow
        from zope.component import getUtility
        from zope.configuration import xmlconfig
        import repoze.bfg.workflow.tests.fixtures as package
        xmlconfig.file('configure.zcml', package, execute=True)
        from repoze.bfg.workflow.tests.fixtures.dummy import Content
        from repoze.bfg.workflow.tests.fixtures.dummy import callback
        content = Content()
        utility = getUtility(IWorkflow, name='theworkflow')
        self.assertEqual(utility.__class__, Workflow)
        self.assertEqual(
            utility._state_order,
            ['private', 'public', None],
            )
        self.assertEqual(
            utility._state_data,
            {u'public': {'description': u'Everybody can see it',
                         'title': u'Public'},
             u'private': {'description': u'Nobody can see it',
                          'title': u'Private'},
             None: {}},
            )
        transitions = utility._transition_data
        self.assertEqual(len(transitions), 3)
        self.assertEqual(transitions[0],
             {'from_state': None, 'callback': callback,
              'name': 'initialize', 'to_state': u'private'},)
        self.assertEqual(transitions[1],
            {'from_state': u'private', 'callback': callback,
              'name': u'to_public', 'to_state': u'public'},)
        self.assertEqual(transitions[2],
             {'from_state': u'public', 'callback': callback,
              'name': 'to_private', 'to_state': u'private'}
            )

class DummyContext:
    info = None
    def __init__(self, **kw):
        self.actions = []
        self.__dict__.update(kw)

class DummyState:
    def __init__(self, name, **extras):
        self.name = name
        self.extras = extras
        
class DummyTransition:
    def __init__(self, name, from_state='private', to_state='public',
                 callback=None, **extras):
        self.name = name
        self.from_state = from_state
        self.to_state = to_state
        self.callback = callback
        self.extras = extras

                  
