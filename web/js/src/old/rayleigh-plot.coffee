d3 = @d3
console = @console

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

class MatrixPlot
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
            x: d3.scale[@scaleType.x]().clamp(yes).range [0, @plotDim.x]
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

    makeZColorMap: ->
        map = @scale.z
        height = @plotDim.y
        colorInterp = d3.interpolateRgb @zColor.lower, @zColor.upper
        (z) -> colorInterp(1.0 - map(z)/height)

    makeZGradient: ->
        @zGradient = describe @canvas.append("defs")
                                     .append("linearGradient"),
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

    prepare: ->
        return if @prepared

        @makeCanvas()
        @makeZGradient()
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

    draw: (x, y, z) ->
        @prepare()

        data = []
        for row in [0...y.length]
            for col in [0...x.length]
                data.push([x[col], y[row], z[row][col]])

        {x: mapX, y: mapY,} = @scale
        mapZ = @makeZColorMap()
        width = Math.round @plotDim.x/x.length
        height = Math.round @plotDim.y/y.length

        rects = @canvas.selectAll("rect#value").data(data)
        describe rects.enter().insert("rect"),
            class: "value"
            x: (d) -> Math.round mapX d[0]
            y: (d) -> Math.round mapY(d[1]) - height
            width: width
            height: height
            stroke: "none"
            fill: (d) -> mapZ d[2]

        rects.transition()
             .duration(1000)
             .attr("fill", (d) -> mapZ d[2])

        @drawn = yes


    refresh: ->
        return unless @prepared

        @canvas.remove()
        @prepared = false
        @drawn = false
        @prepare()
        @draw @data if @drawn

plot = new MatrixPlot("#plot")
plot.setAxisLabel
    x: "Frequency [Hz]"
    y: "Time [s]"
    z: "STD/Mean"
    title: "Rayleigh Statistic"
plot.setLimits
    y: [0, 60]
    x: [0, 8192]
    z: [0, 2]

refreshTime = 10000

updateLatestBlock = ->
    d3.json "rayleigh/blocks/latest?num_frequency_bins=60", (error, json) ->
        if error? or not json.success
            console.log error if error?
            console.log json.error if json?
            setTimeout updateLatestBlock, refreshTime
            return

        {start_time, time_offsets, frequencies, rs} = json.data
        plot.setAxisLabel
            y: "Time [s] since #{start_time}"
        plot.setLimits
            z: d3.extent d3.merge rs
        plot.draw frequencies, time_offsets, rs

        setTimeout updateLatestBlock, refreshTime
updateLatestBlock()
