# Cooperative Amateur Radio Foxhunting using Sheaves
(c) 2019 Michael Robinson

This repository contains sample code demonstrating how to use the PySheaf library to fuse observations of a hidden radio transmitter.

## Organization of the repository
This repository consists of importable python modules `fox_sheaf`, `generate_data`, and several Jupyter notebooks demonstrating how to use it.  

The radio propagation model included is very simple: inverse square law only.  This can be changed easily if desired.  This appears in both of the modules, and is duplicated *intentionally*.  This allows for studies in which the simulated data do not agree with the model used for combining observations.

### Data generator: `generate_data`:
The `generate_data` module defines module defines container classes `ReceptionReport`, `Transmitter`, and `Receiver` for radio observations.  Physically appropriate noise models are included, and noise levels can be selected as desired.  It also contains a small demonstration if the module is run as a script.  

### Sheaf construction: `fox_sheaf`:
The `fox_sheaf` a thin wrapper subclass `FoxSheaf` of the PySheaf `Sheaf` class that performs radio modeling.  This wrapper only defines a new constructor -- all methods are inherited from the PySheaf `Sheaf` class.  The restriction maps of `FoxSheaf` are instances of `SetMorphism` or `LinearMorphism`, given by a Python function instance or a Numpy array instance, respectively.  

### The basics: `fox_sheaf_basics`:
This notebook explains the basics of how to create and manipulate sheaves for fox hunting.  This involves constructing instances of `FoxSheaf` and populating them with data, visualizing the sheaf structure and computing consistency radius.

### Locating a fox from bearings: `bearing_locating`:
This notebook explains how to run optimizations on consistency radius using the `Sheaf.FuseAssignment()` method.  It also has shows how to compute the consistency filtration for this example.

### Noise performance: `noise_performance`:
This notebook explores how noise in the measurements impacts the predicted fox location.

### Consistency filtration: `consistency_filtrations`:
This notebook contains a single example of computing a consistency filtration of a complicated scenario with two fox transmitters and four sensors.