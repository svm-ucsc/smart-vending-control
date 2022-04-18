from main import *

# Create test items
item1_info = {'UID':1, 'name':'Cheetos', 'quantity':'2', 'weight':99.2233,
              'volume':1840.103, 'row':1, 'column':1}
item2_info = {'UID':1, 'name':'Hershey', 'quantity':'1', 'weight': 45,
              'volume': 46.512, 'row':1, 'column':2}
item3_info = {'UID':1, 'name':'Skittles', 'quantity':'1', 'weight': 61.5,
              'volume':34.806, 'row':2, 'column':1}

Cheetos = Item(item1_info)
Hershey = Item(item2_info)
Skittles = Item(item3_info)

order1 = [Cheetos, Hershey, Skittles]
order2 = [Hershey, Skittles, Cheetos]
order3 = [Skittles, Hershey, Cheetos]

# tests for schedule_order
expected = [Cheetos, Hershey, Skittles]
s_order1 = schedule_order(order1)
s_order2 = schedule_order(order2)
s_order3 = schedule_order(order3)
try:
    assert (s_order1[2] == s_order2[2] == s_order3[2] == Skittles)
    print("***PASSED test for schedule order***")
except:
    print("***FAILED test for schedule order***")
    print("\tExpected [Cheetos, Hershey, Skittles] or [Hershey, Cheetos, Skittles]\n")
    print("Actual: {}, {}, {}".format(s_order1, s_order2, s_order3))