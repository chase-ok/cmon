d3 = @d3
console = @console
$ = @jQuery

ifo = @ifo
subsystem = @subsystem
channel = @channel
source = @source
startGPSTime = @startTime
minGPSTime = @minTime
maxGPSTime = @maxTime
startLocalTime = new Date().getTime()/1000
webRoot = @webRoot

describe = (obj, attrs) ->
    for attr, value of attrs
        obj = obj.attr attr, value
    obj

mergeObj = (base, newObj) ->
    base = {} unless base?
    for key, value of newObj
        base[key] = value if value?
    base

isEmpty = (obj) ->
    for prop, value of obj
        if obj.hasOwnProperty prop
            return no
    return yes
    
_triggerCount = 0
class Chunk
    constructor: (@startTime, @endTime) ->
        @accessedTime = 0
        @triggers = []
        @loaded = no
    
    load: (limit=1000, numTries=2) ->
        return unless numTries > 0
        
        @accessedTime = new Date().getTime()
        return if @loaded
        
        url = "#{webRoot}/triggers/#{ifo}/#{subsystem}/#{channel}/" + 
              "#{@startTime}-#{@endTime}?source=#{source}&limit=#{limit}"
        d3.json url, (error, json) =>
            if error? or not json.success
                console.log error if error?
                console.log json.error if json?
                setTimeout (=> @load(limit, numTries-1)), 10
                return
            
            @triggers = json.data.triggers
            for trigger in @triggers
                trigger.id = _triggerCount += 1
            @loaded = yes        
    
class TriggerStore
    constructor: (@timeChunk=30, @maxChunks=50)->
        @chunks = {}
        
    start: ->
        @_intervalId = setInterval @garbageCollect, 10000 unless @_intervalId?
        
    indicateWindow: (startTime, endTime, buffer=2) ->
        for start in @_getChunkStarts startTime, endTime, buffer
            if not @chunks[start]?
                @chunks[start] = new Chunk(start, start + @timeChunk)
            @chunks[start].load()
    
    getWindow: (startTime, endTime, buffer=1) ->
        # Note! Will also return triggers outside of the window!
        starts = @_getChunkStarts startTime, endTime, buffer
        [].concat.apply [], (@chunks[start].triggers for start in starts)
    
    _getChunkStarts: (startTime, endTime, buffer) ->
        lowestTime = @timeChunk*(Math.floor(startTime/@timeChunk) - buffer)
        numChunks = Math.ceil((endTime - startTime)/@timeChunk) + 2*buffer
        
        if numChunks >= @maxChunks
            console.log "Warning! window is too large: #{startTime}-#{endTime}"
        
        lowestTime + i*@timeChunk for i in [0...numChunks]
        
    garbageCollect: ->
        numChunks = 0
        numChunks += 1 for _, _ of @chunks
        numToRemove = numChunks - @maxChunks
        return unless numToRemove > 0
        
        chunksArray = chunk for _, chunk of @chunks
        chunksArray.sort (c1, c2) -> c1.accessedTime - c2.accessedTime
        for chunk in chunksArray[0...numToRemove]
            delete @chunks[chunk.startTime]
    
    stop: ->
        clearInterval @_intervalId if @_intervalId?
        @intervalId = null

class TriggerScroller
    constructor: (@store, @windowSize=30, @rootSelector="body") ->
        @root = d3.select @rootSelector

        @dim = {x: @root.attr("width"), y: @root.attr("height")}
        @margin = {top: 20, right: 50, bottom: 40, left: 50}
        @zBarWidth = 30
        @plotDim = 
            x: @dim.x - @margin.left - @margin.right - @zBarWidth
            y: @dim.y - @margin.top - @margin.bottom

        @setScale()
        @setTicks()
        @setAxisLabel
            x: "Time [s]"
            y: "Frequency [Hz]"
            z: "SNR"
            title: ""
        @setZColor
            lower: d3.rgb "black"
            upper: d3.rgb 255, 0, 0
        @setLimits
            x: [-@windowSize, 0]

        @prepared = false
        @drawn = no
        @showGrid = true

    select: (selector) -> d3.select("#{@rootSelector} #{selector}")

    setScale: (type={x:"linear", y:"linear", z:"linear"}) ->
        @scaleType = mergeObj @scaleType, type
        alreadySet = @scale?
        @scale = 
            x: d3.scale[@scaleType.x]().clamp(no).range [0, @plotDim.x]
            y: d3.scale[@scaleType.y]().clamp(yes).range [@plotDim.y, 0]
            z: d3.scale[@scaleType.z]().clamp(yes).range [@plotDim.y, 0]
        @setLimits() if alreadySet 
        @refresh()

    setLimits: (limits={x: null, y: null, z: null}) ->
        @limits = mergeObj @limits, limits
        @scale.x.domain @limits.x if @limits.x?
        @scale.y.domain @limits.y if @limits.y?
        @scale.z.domain @limits.z if @limits.z?
        @refresh()

    setAxisLabel: (label={x: null, y: null, z: null, title: null}) ->
        @label = mergeObj @label, label
        if @prepared
            @select(".title.axis-label").text @label.title
            @select(".x.axis-label").text @label.x
            @select(".y.axis-label").text @label.y
            @select(".z.axis-label").text @label.z

    setTicks: (format={x: null, y: null, z: null}) ->
        @ticks = mergeObj @ticks, format
        @refresh()

    setZColor: (colors={lower: null, upper: null}) ->
        @zColor = mergeObj @zColor, colors
        @refresh()

    makeAxis: ->
        make = (orient, type, ticks) ->
            axis = d3.svg.axis().scale(type).orient(orient)
            axis.ticks(ticks...) if ticks?
            axis
        x: make "bottom", @scale.x, @ticks.x
        y: make "left", @scale.y, @ticks.y
        z: make "right", @scale.z, @ticks.z

    makeCanvas: ->
        @canvas = describe @root.append("g"),
            transform: "translate(#{@margin.left}, #{@margin.top})"
        @defs = @canvas.append("defs")

    makeZColorMap: ->
        map = @scale.z
        height = @plotDim.y
        colorInterp = d3.interpolateRgb @zColor.lower, @zColor.upper
        (z) -> colorInterp(1.0 - map(z)/height)

    makeZGradient: ->
        @zGradient = describe @defs.append("linearGradient"),
            id: "zGradient"
            x1: "0%"
            y1: "100%"
            x2: "0%"
            y2: "0%"

        @zGradientStart = describe @zGradient.append("stop"),
            offset: "0%"
            "stop-color": @zColor.lower
            "stop-opacity": 1

        @zGradientStop = describe @zGradient.append("stop"),
            offset:"100%"
            "stop-color": @zColor.upper
            "stop-opacity": 1

    makePlotClipPath: ->
        @plotClipId = "plotClip"
        @plotClip = @canvas.append("clipPath").attr("id", @plotClipId)
        describe @plotClip.append("rect"),
            x: 0
            y: 0
            width: @plotDim.x
            height: @plotDim.y

    prepare: ->
        return if @prepared

        @makeCanvas()
        @makeZGradient()
        @makePlotClipPath()
        @drawGrid()
        @drawAxis()
        @drawAxisLabels()
        @drawZColorBar()
        
        @prepared = true

    drawAxis: ->
        axis = @makeAxis()
        (describe @canvas.append("g"),
            class: "x axis"
            transform: "translate(0, #{@plotDim.y})"
        ).call(axis.x)
        (describe @canvas.append("g"),
            class: "y axis"
        ).call(axis.y)
        (describe @canvas.append("g"),
            class: "z axis"
            transform: "translate(#{@plotDim.x + @zBarWidth}, 0)"
        ).call(axis.z)
        
     drawGrid: ->
        return unless @showGrid

        axis = @makeAxis()
        axis.x.tickSize(-@plotDim.y, 0, 0).tickFormat("")
        axis.y.tickSize(-@plotDim.x, 0, 0).tickFormat("")
        
        (describe @canvas.append("g"),
            class: "x grid"
            transform: "translate(0, #{@plotDim.y})"
        ).call(axis.x)
        (describe @canvas.append("g"),
            class: "y grid"
        ).call(axis.y)

    drawAxisLabels: ->
        describe @canvas.append("text").text(@label.title),
            x: @plotDim.x/2
            y: -@margin.top + 10
            "text-anchor": "middle"
            class: "title axis-label"

        describe @canvas.append("text").text(@label.x),
            x: @plotDim.x/2
            y: @plotDim.y + @margin.bottom - 5
            "text-anchor": "middle"
            class: "x axis-label"

        rotated = @canvas.append("g").attr "transform", "rotate(-90)"
        describe rotated.append("text").text(@label.y),
            x: -@plotDim.y/2
            y: 10-@margin.left
            "text-anchor": "middle"
            class: "y axis-label"

        describe rotated.append("text").text(@label.z),
            x: -@plotDim.y/2
            y: @plotDim.x+@zBarWidth+@margin.right
            "text-anchor": "middle"
            class: "z axis-label"

    drawZColorBar: ->
        spacing = 10
        describe @canvas.append("rect"),
            x: @plotDim.x+spacing
            y: 0
            width: @zBarWidth-spacing
            height: @plotDim.y
            fill: "url(#zGradient)"

    scrollTo: (gpsTime, animateDuration=null) ->
        lastTime = if @lastTime? then @lastTime else gpsTime
        animateDuration = 1000*(gpsTime - lastTime) unless animateDuration?
        @setAxisLabel
            x: "Time [s] since #{Math.round gpsTime}"
        
        scrollWindow = [gpsTime - @windowSize, gpsTime]
        @store.indicateWindow scrollWindow...
        
        timeOffset = (trigger, time) -> 
            trigger.start_time + trigger.start_time_ns*1e-9 - time
        
        {x: mapX, y: mapY} = @scale
        mapZ = @makeZColorMap()
        widthScale = @plotDim.x/@windowSize
        
        triggers = @store.getWindow scrollWindow...
        rects = @canvas.selectAll("rect.value")
                       .data(triggers, (trigger) -> trigger.id)
        
        describe rects.enter().append("rect"),
            class: "value"
            x: (trigger) -> Math.round mapX timeOffset trigger, lastTime
            y: (trigger) -> 
                Math.round mapY (trigger.central_freq - trigger.bandwidth/2)
            width: (trigger) -> Math.ceil widthScale*trigger.duration
            height: (trigger) ->
                halfBand = trigger.bandwidth/2
                # need to use mapY in case of logarithmic freq scale
                diff = mapY(trigger.central_freq - halfBand) - 
                       mapY(trigger.central_freq + halfBand)
                Math.ceil Math.abs diff
            stroke: "none"
            fill: (trigger) -> mapZ trigger.snr
            "clip-path": "url(##{@plotClipId})"
            
        rects.exit().remove()
        
        describe rects.transition().duration(animateDuration).ease("linear"),
             x: (trigger) -> Math.round mapX timeOffset trigger, gpsTime
        
        @lastTime = gpsTime

    refresh: ->
        # TODO: this is not appropriately named!
        return unless @prepared

        @canvas.remove()
        @prepared = false
        @prepare()
        
    startAutoRefresh: (period=1000) ->
        lastTime = @lastTime
        update = =>
            @scrollTo @lastTime, 0 unless lastTime != @lastTime
            lastTime = @lastTime
        @_autoRefreshId = setInterval update, period
        
    stopAutoRefresh: ->
        clearInterval @_autoRefreshId if @_autoRefreshId?
        
    startMouseScroll: (@lastTime) ->
        @prepare()
        
        mouse = {x: @plotDim.x/2, y: @plotDim.y/2}
        @canvas.on "mouseover", ->
            [mouse.x, mouse.y] = d3.mouse this
        
        bound = {left: 100, right: @plotDim.x - 100}
        update = =>
            time = @lastTime
            if mouse.x < bound.left
                time -= 0.05*(bound.left - mouse.x)
            else if mouse.x > bound.right
                time += 0.05*(mouse.x - bound.right)
            if time != @lastTime
                @scrollTo time, 500
        setInterval update, 500
        
    startKeyScroll: (@lastTime=startGPSTime) ->
        @prepare()
        
        down = {left: no, right: no}
        d3.select("body").on "keydown", ->
            if d3.event.keyCode is 37 # left arrow
                down.left = yes
            else if d3.event.keyCode is 39
                down.right = yes
        d3.select("body").on "keyup", ->
            if d3.event.keyCode is 37
                down.left = no
            else if d3.event.keyCode is 39
                down.right = no
        
        update = =>
            time = @lastTime
            if down.left
                time -= 1.0
            else if down.right
                time += 1.0
            if time != @lastTime
                @scrollTo time, 300
        setInterval update, 300
    
    startTimeScroll: (@lastTime=startGPSTime) ->
        @prepare()
        localTime = new Date().getTime()/1000
        update = =>
            newLocalTime = new Date().getTIme()/1000
            timeDiff = 
            time = @lastTime
            if down.left
                time -= 1.0
            else if down.right
                time += 1.0
            if time != @lastTime
                @scrollTo time, 300
        setInterval update, 300

makeTimeSlider = (scroller, time=startGPSTime) ->
    $("#time-slider").slider
        min: minGPSTime
        max: maxGPSTime
        value: time
        change: (event, ui) ->
            scroller.scrollTo ui.value, 500

$ ->
    store = new TriggerStore()
    store.start()
    store.indicateWindow startGPSTime, startGPSTime + 30
    
    scroller = new TriggerScroller(store, 30, "#plot")
    scroller.setScale
        y: "log"
        z: "log"
    scroller.setAxisLabel
        title: "Triggers [#{source}]"
    scroller.setLimits
        y: [1000, 5000]
        z: [10, 200]
    scroller.prepare()
    
    scroller.scrollTo startGPSTime
    scroller.startAutoRefresh()
    scroller.startKeyScroll startGPSTime
    makeTimeSlider scroller
