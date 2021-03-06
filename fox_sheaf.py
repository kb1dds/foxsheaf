# Sheaf construction for radio foxhunting
# (c) 2019 Michael Robinson

import numpy as np
import pysheaf as ps

# Useful functions
def freespace(power,distance):
    """Compute free space power loss as a function of distance using the inverse square law model"""
    return power/(4*np.pi*distance**2)

def freespace_restrict(array_in):
    """Restriction map for the sheaf in which Received Signal Strength Indication (RSSI) is measured.  This computes RSSI based on transmitter and receiver location"""
    return np.array([array_in[2],array_in[3],freespace(array_in[4],np.linalg.norm(array_in[0:2]-array_in[2:4]))])

def bearing(tx_location,rx_location):
    """Compute a bearing from receiver to the transmitter given their locations"""
    return np.arctan2(tx_location[0]-rx_location[0],tx_location[1]-rx_location[1])

def bearing_restrict(array_in):
    """Restriction map for the sheaf in which bearing is measured.  This computes bearing based on transmitter and receiver location"""
    return np.array([array_in[2],array_in[3],180/np.pi*bearing(array_in[0:2],array_in[2:4])])

def bearing_metric(array1,array2):
    """The metric on the space of bearings, which computes distance between angles in degrees""" 
    m=np.linalg.norm(array1[0:2]-array2[0:2])
    anglediff=abs(array1[2]-array2[2])
    if anglediff>180:
        anglediff=360-anglediff
    return (m+anglediff)

class SetMorphism():
  """A morphism in a subcategory of Set, described by a function object"""
  def __init__(self,fcn):
      """Set morphisms are constructed from a function object"""
      self.fcn=fcn

  def __mul__(self,other):
      """Composition of morphisms"""
      return SetMorphism(lambda x : self.fcn(other.fcn(x)))

  def __call__(self,arg):
      """Calling the morphism on an element of the set"""
      return self.fcn(arg)

class LinearMorphism(SetMorphism):
  """A morphism in a category that has a matrix representation.  This is a subclass of SetMorphism, because matrices are also functions (linear transformations of vectors)"""
  def __init__(self,matrix):
      """Linear morphisms are constructed from a numpy array object"""
      self.matrix=matrix
      SetMorphism.__init__(self,lambda x: np.dot(matrix,x))

  def __mul__(self,other):
      """Composition of linear morphisms is matrix multiplication.  But this also defines composition of the linear transformations"""
      try: # Try to multiply matrices.  This might fail if the other morphism isn't a LinearMorphism
         return LinearMorphism(np.dot(self.matrix, other.matrix))
      except AttributeError:
         return SetMorphism.__mul__(self,other)
     
class FoxSheaf(ps.Sheaf):
    def __init__(self,rx_types=None,rxs=None):
        """Construct a foxhunting sheaf with a single receptionAssignment from a list of Receiver instances. This sheaf is suitable for asynchronous data.  rx_types is a list of strings, either 'bearing' or 'rssi', telling the capabilities of each receiver.  Note that although this constructor expects to unpack Receiver instances as defined in the generate_data module, it will happily consume anything supporting that API"""
        ps.Sheaf.__init__(self)
        
        if (rx_types is None) or (rxs is None):
            return
        
        self.rx_types=rx_types
        self.rx_names=[]
        self.rx_cellidx=[]

        # Use Euclidean distance for aggregating consistency radius throughout
        self.mNumpyNormType=2
        self.mPreventRedundantExtendedAssignments=False # Usually, you want this behavior!  It's redundant because this is also the PySheaf default
        
        ## Sheaf construction begins here!
        # It is perhaps a little confusing, but cells are indexed by integers.  I do this because I want to the construction to scale cleanly with more or fewer receivers.  (I could do this differently, but it'll do!)
        
        # Each cell is added according the the following pattern:
        # First, create the cell with its appropriate stalk "dimension".  In PySheaf "dimension" means merely the number of free parameters it takes to specify the data.  PySheaf will happily work with stalks of non-numeric data, but numpy arrays are all we need here.
        # Second, cells with virtual observations are marked with mOptimizationCell = True.  True observations (made by sensors) are marked with mOptimizationCell = False.  This instructs PySheaf that it is not allowed to alter an assignment supported on a true observations
        
        # Third, the stalks are given an assignment.  If it's a true observation, this is used.  Virtual observations are given random initial value.  This will certainly be overwritten by an optimization step, later, but most optimizers want an initial guess.
        
        # Cofaces (= restrictions) are created along with the cells.  Although the resulting sheaf is a sheaf of Sets, wherever the restrictions happen to be linear, we use LinearMorphisms.  This has a dual purpose: (1) it's just plain easier to read and (2) if you happen to want a subsheaf that happens to be all LinearMorphisms, then it will automatically be interpreted sheaf of vector spaces.  (Yay duck typing!)

        self.AddCell(0, # 0: Fox location and power level 
                     ps.Cell('foxloc_power',
                             dataDimension=3))
        self.GetCell(0).mOptimizationCell = True
        self.GetCell(0).SetDataAssignment(ps.Assignment('foxloc_power',
                                                        np.random.randn((3))))
                                                       
        self.AddCell(1, # 1: Fox location only
                     ps.Cell('foxloc',
                             dataDimension=2))
        self.GetCell(1).mOptimizationCell = True
        self.GetCell(1).SetDataAssignment(ps.Assignment('foxloc',
                                                        np.random.randn(2)))
        
        self.AddCoface(0,1,
                       ps.Coface('foxloc_power','foxloc',LinearMorphism(np.array([[1,0,0],
                                                                                  [0,1,0]]))))
        
        idx=2 # Current cell index
        for rx_type,rx in zip(rx_types,rxs):
            if rx_type == 'bearing':
                for i,r in enumerate(rx.reception_reports):
                    self.AddCell(idx,
                                 ps.Cell('foxloc_rxloc',
                                         dataDimension=4))
                    self.GetCell(idx).mOptimizationCell = True
                    self.GetCell(idx).SetDataAssignment(ps.Assignment('foxloc_rxloc',
                                                                      np.array([np.random.randn(1)[0],
                                                                                np.random.randn(1)[0],
                                                                                r.location[0],
                                                                                r.location[1]])))
                    self.AddCell(idx+1,
                                 ps.Cell('bearing_rxloc',
                                         dataDimension=3,
                                         compareAssignmentsMethod=bearing_metric))
                    self.GetCell(idx+1).SetDataAssignment(ps.Assignment('bearing_rxloc',
                                                                        np.array([r.location[0],
                                                                                  r.location[1],
                                                                                  r.bearing])))
                    self.GetCell(idx+1).mOptimizationCell=False
                    
                    self.AddCoface(idx,idx+1,
                                   ps.Coface('foxloc_rxloc','bearing_rxloc',
                                             SetMorphism(bearing_restrict)))
                    self.AddCoface(idx,1,
                                   ps.Coface('foxloc_rxloc','foxloc',
                                             LinearMorphism(np.array([[1,0,0,0],
                                                                      [0,1,0,0]]))))
                    
                    idx += 2
            elif rx_type == 'rssi':
                for i,r in enumerate(rx.reception_reports):
                    self.AddCell(idx,
                                 ps.Cell('foxloc_power_rxloc',
                                         dataDimension=5))
                    self.GetCell(idx).mOptimizationCell = True
                    self.GetCell(idx).SetDataAssignment(ps.Assignment('foxloc_power_rxloc',
                                                                      np.array([np.random.randn(1)[0],
                                                                                np.random.randn(1)[0],
                                                                                r.location[0],
                                                                                r.location[1],
                                                                                r.rssi])))
                    self.AddCell(idx+1,
                                 ps.Cell('rssi_rxloc',
                                         dataDimension=3))
                    self.GetCell(idx+1).SetDataAssignment(ps.Assignment('rssi_rxloc',
                                                                        np.array([r.location[0],
                                                                                  r.location[1],
                                                                                  r.rssi])))
                    self.GetCell(idx+1).mOptimizationCell=False

                    self.AddCoface(idx,idx+1,
                                   ps.Coface('foxloc_power_rxloc','rssi_rxloc',
                                             SetMorphism(freespace_restrict)))
                    self.AddCoface(idx,0,
                                   ps.Coface('foxloc_power_rxloc','foxloc_power',
                                             LinearMorphism(np.array([[1,0,0,0,0],
                                                                      [0,1,0,0,0],
                                                                      [0,0,0,0,1]]))))
                    
                    idx += 2
            else:
                raise(NotImplementedError)
