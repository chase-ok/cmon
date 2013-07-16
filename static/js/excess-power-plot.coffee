d3 = @d3
console = @console

ifo = @ifo
subsystem = @subsystem
channel = @channel
startGPSTime = @startTime
startLocalTime = new Date().getTime()/1000
root = @root

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

class BurstPlot
    constructor: (@rootSelector="body") ->
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
            x: "x"
            y: "y"
            z: "z"
            title: ""
        @setZColor
            lower: d3.rgb "black"
            upper: d3.rgb 255, 0, 0

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

    draw: (gpsTime, bursts) ->
        @prepare()

        totalTime = Math.abs @limits.x[0] - @limits.x[1]
        totalBandwidth = Math.abs @limits.y[0] - @limits.y[1]

        {x: mapX, y: mapY} = @scale
        mapZ = @makeZColorMap()
        mapTime = (seconds, ns) ->
            mapX (seconds + ns*1e-9 - gpsTime)

        getWidth = (duration) => Math.ceil @plotDim.x*(duration/totalTime)
        getHeight = (fMin, fMax) => Math.abs mapY(fMax) - mapY(fMin)

        for burst in bursts
            x0 = mapTime(burst.start_time, burst.start_time_ns)
            halfBand = burst.bandwidth/2
            fCenter = burst.central_freq
            [fMin, fMax] = [fCenter - halfBand, fCenter + halfBand]
            
            rect = @canvas.insert "rect"
            rect.datum burst

            describe rect,
                class: "value"
                x: x0
                y: mapY fMax
                width: getWidth(burst.duration)
                height: getHeight(fMin, fMax)
                stroke: "none"
                opacity: "1.0"
                fill: mapZ(burst.confidence)
                "clip-path": "url(##{@plotClipId})"
            
            rect.style "shape-rendering", "crispEdges"

            rect.transition()
                 .duration(1000*(totalTime + burst.start_time + burst.start_time_ns*1e-9 - gpsTime + burst.duration))
                 .ease("linear")
                 .attr("x", -getWidth(burst.duration))
                 .each("end", () -> d3.select(this).remove())

        @drawn = yes


    refresh: ->
        return unless @prepared

        @canvas.remove()
        @prepared = false
        @drawn = false
        @prepare()
        @draw @data if @drawn

plot = new BurstPlot("#plot")
plot.setScale
    z: "log"
plot.setAxisLabel
    x: "Time [s]"
    y: "Frequency [Hz]"
    z: "Confidence"
    title: "Excess Power Bursts"
plot.setLimits
    y: [1, 5000]
    x: [-30, 0]
    z: [10, 30]

lastGPSTime = Math.floor startGPSTime
lastLocalTime = startLocalTime
refreshTime = 5000
timerStarted = no

updateTime = ->
    timerStarted = yes
    gpsTime = startGPSTime + (new Date().getTime()/1000 - startLocalTime)
    plot.setAxisLabel
        x: "Time [s] since #{Math.round gpsTime}"
    setTimeout updateTime, 1000

updateBursts = ->
    newLocalTime = new Date().getTime()/1000
    newGPSTime = lastGPSTime + (newLocalTime - lastLocalTime)
    console.log "#{root}/excesspower/#{subsystem}/#{channel}/bursts/#{Math.floor(lastGPSTime)}-#{Math.floor(newGPSTime)}"

    d3.json "#{root}/excesspower/#{subsystem}/#{channel}/bursts/#{Math.floor(lastGPSTime)}-#{Math.floor(newGPSTime)}?limit=100", (error, json) ->
        if error? or not json.success
            console.log error if error?
            console.log json.error if json?
            setTimeout updateBursts, refreshTime
            return

        {bursts} = json.data
        console.log "TIME #{lastGPSTime}"
        console.log "#Bursts #{bursts.length}"
        plot.draw lastGPSTime, bursts

        
        lastGPSTime = newGPSTime
        lastLocalTime = newLocalTime
        setTimeout updateBursts, refreshTime

        updateTime() unless timerStarted

updateBursts()