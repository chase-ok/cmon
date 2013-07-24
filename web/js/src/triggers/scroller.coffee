define ['utils', 'plots','d3'], (utils, plots, d3) ->
    {describe, IntervalFunc} = utils
    
    class TriggerScroller extends plots.ZColorPlot
        constructor: (@store, rootSelector) ->
            super rootSelector
            
            @windowSize 30
            @_autoRefresh = new IntervalFunc()
            @_nouseScroll = new IntervalFunc()
            @_keyScroll = new IntervalFunc()
            @axisLabels
                x: "Time [s]"
                y: "Frequency [Hz]"
                z: "SNR"
            @limits
                x: [-@_windowSize, 0]
                
        windowSize: (windowSize) ->
            if windowSize?
                @_windowSize = windowSize
                @limits
                    x: [-windowSize, 0]
                @declareDirty()
                this
            else
                @_windowSize
    
        scrollTo: (time, animateDuration=null) ->
            @prepare()
            
            lastTime = if @_lastTime? then @_lastTime else time
            animateDuration = 1000*(time - lastTime) unless animateDuration?
            @axisLabels
                x: "Time [s] since #{Math.round time}"
            
            windowSize = @windowSize()
            scrollWindow = [time - windowSize, time]
            @store.indicateWindow scrollWindow...
            
            timeOffset = (trigger, time) -> 
                trigger.start_time + trigger.start_time_ns*1e-9 - time
            
            maps = @maps()
            widthScale = @canvasSize.x/windowSize
            
            triggers = @store.getWindow scrollWindow...
            rects = @canvas.selectAll("rect.value")
                           .data(triggers, (trigger) -> trigger.id)
            
            describe rects.enter().append("rect"),
                class: "value"
                x: (trigger) -> 
                    Math.round maps.x timeOffset trigger, lastTime
                y: (trigger) ->
                    freqMax = trigger.central_freq - trigger.bandwidth/2
                    Math.round maps.y freqMax
                width: (trigger) -> 
                    Math.ceil widthScale*trigger.duration
                height: (trigger) ->
                    halfBand = trigger.bandwidth/2
                    # need to use mapY in case of logarithmic freq scale
                    diff = maps.y(trigger.central_freq - halfBand) - 
                           maps.y(trigger.central_freq + halfBand)
                    Math.ceil Math.abs diff
                fill: (trigger) -> 
                    maps.z trigger.snr
                stroke: "none"
                "clip-path": "url(##{@canvasClipId})"
                
            rects.exit().remove()
            
            describe rects.transition()
                          .duration(animateDuration)
                          .ease("linear"),
                 x: (trigger) -> Math.round maps.x timeOffset trigger, time
            
            @_lastTime = time
        
        autoRefresh: (autoRefresh, period=1000) ->
            if autoRefresh?
                @_autoRefresh.running no
                
                if autoRefresh
                    @_autoRefresh.period period
                    
                    lastTime = @_lastTime
                    @_autoRefresh.func =>
                        @scrollTo @_lastTime, 0 unless lastTime != @_lastTime
                        lastTime = @_lastTime
                        
                    @_autoRefresh.running yes
                this
            else
                @_autoRefresh.running()
                
        mouseScroll: (mouseScroll, period=500, scrollRate=0.05, region=100) ->
            if mouseScroll?
                @_mouseScroll.running no
                
                if mouseScroll
                    @_mouseScroll.period = period
                    
                    mouse = {x: @canvasSize.x/2, y: @canvasSize.y/2}
                    @canvas.on "mouseover", ->
                        [mouse.x, mouse.y] = d3.mouse this
                    bound = {left: region, right: @canvasSize.x - region}
                    @_mouseScroll.func =>
                        time = @_lastTime
                        if mouse.x < bound.left
                            time -= scrollRate*(bound.left - mouse.x)
                        if mouse.x > bound.right
                            time += scrollRate*(mouse.x - bound.right)
                        if time != @_lastTime then @scrollTo time, period
                        
                    @_mouseScroll.running yes
                this    
            else
                @_mouseScroll.running()
                
        keyScroll: (keyScroll, period=300, rate=1.0, left=37, right=39) ->
            if keyScroll?
                @_keyScroll.running no
                
                if keyScroll
                    @_keyScroll.period period
                    
                    down = {left: no, right: no}
                    d3.select("body").on "keydown", ->
                        if d3.event.keyCode is left then down.left = yes
                        if d3.event.keyCode is right then down.right = yes
                    d3.select("body").on "keyup", ->
                        if d3.event.keyCode is left then down.left = no
                        if d3.event.keyCode is right then down.right = no
                    @_keyScroll.func =>
                        time = @_lastTime
                        if down.left then time -= rate
                        if down.right then time += rate
                        if time != @_lastTime then @scrollTo time, period
                    
                    @_keyScroll.running yes
                this    
            else
                @_keyScroll.running()
    
    return {TriggerScroller}