class State:
  """Parent class of state machine states"""
  def __init__(self, start, current, previous):
    self.start = start
    self.current = current
    self.previous = previous
  
  def get_next(self):
    """Poll for variable changes and select next state accordingly"""
    pass
    
class Idle(State):
  """Low Power state"""
  def __init__(self, start, current, previous):
    pass
    
class BootUp(State)
  """Transition to full power"""
  def __init__(self, start, current, previous):
    pass
    
class Selection(State)
  """User interacting with screen"""
  def __init__(self, start, current, previous):
    pass
    
class Authentication(State)
  """Authenticate user prior to loading"""
  def __init__(self, start, current, previous):
    pass
    
class ItemLoading(State)
  """User loads item into machine"""
  def __init__(self, start, current, previous):
    pass

class Payment(State)
  """Obtains payment from user"""
  def __init__(self, start, current, previous):
    pass
    
class Dispense(State)
  """Move platform and dispense items"""
  def __init__(self, start, current, previous):
    pass

class Reset(State)
  """Refresh inventory counts and reset vending machine"""
  def __init__(self, start, current, previous):
    pass
    

