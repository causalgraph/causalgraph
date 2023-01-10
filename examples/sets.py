def add_cg_example_individuals(G, setname):
    # TODO: Change the way this works entirely. But for now this stays like that.
    """Adds a standard set of CausalNodes and CausalEdges to a given causalgraph.Graph.
        Please choose between those sets: [flat_tire, ...]

    Args:
        G (causalgraph.Graph): The Graph we want to add nodes and edges from a given set.
        setname (str): Name of the set.
    """
    if setname == "flat_tire":
        G.add.causal_node('noise')              # Event
        G.add.causal_node('bumpy_feeling')      # State
        G.add.causal_node('steering_problems')  # Event
        G.add.causal_node('glass_on_road')      # Event
        G.add.causal_node('flat_tire')          # State
        G.add.causal_node('thorns_on_road')     # Event
        G.add.causal_edge('flat_tire',      'noise',            'noise_flat_tire')              # has_cause flat_tire, has_effect noise
        G.add.causal_edge('flat_tire',      'bumpy_feeling',    'bumpy_feeling_flat_tire')      # has_cause flat_tire, has_effect bumpy_feeling
        G.add.causal_edge('flat_tire',      'steering_problems','steering_problems_flat_tire')  # has_cause flat_tire, has_effect steering_problems
        G.add.causal_edge('glass_on_road',  'flat_tire',        'glass_flat_tire')              # has_cause glass_on_road, has_effect flat_tire
        G.add.causal_edge('thorns_on_road', 'flat_tire',        'thorns_flat_tire')           # has_cause thorns_on_road, has_effect flat_tire
    if setname == "prod_sys":
        G.add.causal_node('productDemand')          # Variable
        G.add.causal_node('OrderIn')                # Event
        G.add.causal_node('Producing')              # State
        G.add.causal_node('storageCount')           # Variable
        G.add.causal_node('HeaterOn')               # State
        G.add.causal_node('OrderSupplierA')         # Event
        G.add.causal_node('OrderSupplierB')         # Event
        G.add.causal_node('Temperature')            # Variable
        G.add.causal_node('warmUpTime')             # Event
        G.add.causal_node('PartFinished')           # Event
        G.add.causal_node('materialQuality')        # Event
        G.add.causal_node('formError')              # Event
        G.add.causal_node('Reworking')              # State
        G.add.causal_node('reworked_formError')     # Event
        G.add.causal_node('partsWasted')            # Variable
        G.add.causal_node('partsProduced')          # Variable
        G.add.causal_edge('productDemand', 'OrderIn', 'productDemand->OrderIn', confidence=0.35, time_lag_s=2)   
        G.add.causal_edge('OrderIn', 'Producing', 'OrderIn->Producing')   
        G.add.causal_edge('OrderIn', 'storageCount', 'OrderIn->storageCount')   
        G.add.causal_edge('Producing', 'HeaterOn', 'Producing->HeaterOn')   
        G.add.causal_edge('storageCount', 'storageCount', 'storageCount->storageCount', confidence=0.3, time_lag_s=1)   
        G.add.causal_edge('storageCount', 'OrderSupplierA', 'storageCount->OrderSupplierA')   
        G.add.causal_edge('storageCount', 'OrderSupplierB', 'storageCount->OrderSupplierB')   
        G.add.causal_edge('HeaterOn', 'Temperature', 'HeaterOn->Temperature', confidence=0.2, time_lag_s=0.5)   
        G.add.causal_edge('HeaterOn', 'warmUpTime', 'HeaterOn->warmUpTime')   
        G.add.causal_edge('OrderSupplierA', 'storageCount', 'OrderSupplierA->storageCount')   
        G.add.causal_edge('OrderSupplierA', 'materialQuality', 'OrderSupplierA->materialQuality')   
        G.add.causal_edge('OrderSupplierB', 'storageCount', 'OrderSupplierB->storageCount')   
        G.add.causal_edge('OrderSupplierB', 'materialQuality', 'OrderSupplierB->materialQuality')     
        G.add.causal_edge('Temperature', 'Temperature', 'Temperature->Temperature')   
        G.add.causal_edge('Temperature', 'HeaterOn', 'Temperature->HeaterOn')   
        G.add.causal_edge('Temperature', 'PartFinished', 'Temperature->PartFinished', confidence=1, time_lag_s=2.5)   
        G.add.causal_edge('Temperature', 'Producing', 'Temperature->Producing')   
        G.add.causal_edge('warmUpTime', 'formError', 'warmUpTime->formError')   
        G.add.causal_edge('PartFinished', 'formError', 'PartFinished->formError')   
        G.add.causal_edge('materialQuality', 'formError', 'materialQuality->formError', confidence=0.2, time_lag_s=5)   
        G.add.causal_edge('formError', 'Reworking', 'formError->Reworking')   
        G.add.causal_edge('formError', 'partsProduced', 'formError->partsProduced')   
        G.add.causal_edge('Reworking', 'reworked_formError', 'Reworking->reworked_formError')   
        G.add.causal_edge('reworked_formError', 'partsWasted', 'reworked_formError->partsWasted')   
        G.add.causal_edge('reworked_formError', 'partsProduced', 'reworked_formError->partsProduced')   
        G.add.causal_edge('partsWasted', 'partsWasted', 'partsWasted->partsWasted', confidence=1, time_lag_s=3)   
        G.add.causal_edge('partsProduced', 'partsProduced', 'partsProduced->partsProduced')
    else:
        print("There is no such set of individuals.")

