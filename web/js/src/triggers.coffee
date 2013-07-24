define ['utils', 
        'triggers/scroller', 
        'triggers/store',
        'triggers/densities',
        'jquery'], 
(utils, scroller, store, densities, $) ->
    console.log 'hello world!'
    startTime = utils.definitions.startTime
    
    $ ->
        store = new store.TriggerStore()
        store.garbageCollecting yes
        store.indicateWindow startTime, startTime + 30
        
        scroller = new scroller.TriggerScroller store, "#triggers"
        scroller.windowSize 30
        scroller.scales
            y: d3.scale.log().clamp yes
            z: d3.scale.log().clamp yes
        scroller.title "Triggers [#{utils.definitions.source}]"
        scroller.limits
            y: [1000, 5000]
            z: [10, 200]
            
        scroller.scrollTo startTime
        scroller.autoRefresh yes
        scroller.keyScroll yes
        
        densityPlot = new densities.DensityPlot "#densities"
        densityPlot.scroller scroller
        densityPlot.load()