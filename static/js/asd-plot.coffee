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

class Plot
    constructor: (@rootSelector="body") ->
        @root = d3.select @rootSelector

        @dim = {x: @root.attr("width"), y: @root.attr("height")}
        @margin = {top: 20, right: 20, bottom: 40, left: 50}
        @plotDim = 
            x: @dim.x - @margin.left - @margin.right
            y: @dim.y - @margin.top - @margin.bottom

        @setScale()
        @setTicks()
        @setDefined()
        @setAccessor
            x: (d) -> d[0]
            y: (d) -> d[1]
        @setLabel
            x: "x"
            y: "y"
            title: ""

        @prepared = false
        @drawn = false
        @showGrid = true

    select: (selector) -> d3.select("#{@rootSelector} #{selector}")

    logLog: -> @setScale({x: "log", y: "log"})
    semilogX: -> @setScale({x: "log", y: "linear"})
    semilogY: -> @setScale({x: "linear", y: "log"})

    setScale: (type={x:"linear", y:"linear"}) ->
        @scaleType = mergeObj @scaleType, type
        alreadySet = @scale?
        @scale = 
            x: d3.scale[@scaleType.x]().clamp(yes).range [0, @plotDim.x]
            y: d3.scale[@scaleType.y]().clamp(yes).range [@plotDim.y, 0]
        @setLimits() if alreadySet 
        @refresh()

    setLimits: (limits={x: null, y: null}) ->
        @limits = mergeObj @limits, limits
        @scale.x.domain @limits.x if @limits.x?
        @scale.y.domain @limits.y if @limits.y?
        @refresh()

    setAccessor: (accessor={x: null, y: null}) ->
        @accessor = mergeObj @accessor, accessor
        @refresh() if @drawn

    setLabel: (label={x: null, y: null, title: null}) ->
        @label = mergeObj @label, label
        if @prepared
            @select(".title.axis-label").text @label.title
            @select(".x.axis-label").text @label.x
            @select(".y.axis-label").text @label.y

    setTicks: (format={x: null, y: null}) ->
        @ticks = mergeObj @ticks, format
        @refresh()

    setDefined: (@defined=null) ->
        @refresh

    makeAxis: ->
        make = (orient, type, ticks) ->
            axis = d3.svg.axis().scale(type).orient(orient)
            axis.ticks(ticks...) if ticks?
            axis
        x: make "bottom", @scale.x, @ticks.x
        y: make "left", @scale.y, @ticks.y

    makeLine: ->
        @line = d3.svg.line()

        {x: mapX, y: mapY} = @scale
        {x: accessX, y: accessY} = @accessor
        @line.x((d) -> mapX accessX d)
        @line.y((d) -> mapY accessY d)

        @line.defined @defined if @defined?

    makeCanvas: ->
        @canvas = describe @root.append("g"),
            transform: "translate(#{@margin.left}, #{@margin.top})"

    prepare: ->
        return if @prepared

        @makeCanvas()
        @makeLine()
        @drawGrid()
        @drawAxis()
        @drawLabels()
        
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

    drawLabels: ->
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

    draw: (@data) ->
        @prepare()

        pathData = @line @data
        if @drawn
            @select("path.line")
                .transition()
                .duration(500)
                .attr("d", pathData)
        else
            describe @canvas.append("path"),
                class: "line"
                d: pathData
        @drawn = true

    refresh: ->
        return unless @prepared

        @canvas.remove()
        @prepared = false
        @drawn = false
        @prepare()
        @draw @data if @drawn

plot = new Plot("#plot1")
plot.logLog()
plot.setLabel
    x: "Frequency [Hz]"
    y: "Strain Amplitude [Hz^{-1/2}]"
    title: "Amplitude Spectral Density"
plot.setTicks
    x: [10, d3.format "n"]
    y: [10]
plot.setLimits
    x: [1, 1e4]
    y: [1e-25, 1e-16]
plot.setDefined (d) ->
    d[0] != 0 and not isNaN d[1]

update = ->
    d3.json "asd/data", (error, json) ->
        if error?
            console.log error
            setTimeout update, 10*1000
            return

        {time, frequency, amplitude} = json
        data = ([+frequency[i], +amplitude[i]]\
                for i in [0..frequency.length])
        plot.setLabel
            title: "Time = #{time}"
        plot.draw data

        setTimeout update, 10*1000
update()

# d3.json "asd/data", (error, json) ->
#     {time, frequency, amplitude} = json
#     data = ({freq: +frequency[i], ampl: +amplitude[i]}\
#             for i in [0..frequency.length])

#     plot.setLimits 
#         x: [1, d3.max frequency]
#         y: [1e-24, d3.max amplitude]

#     plot.setAccessor
#         x: (d) -> d.freq
#         y: (d) -> d.ampl

#     plot.defined = (d) -> d.freq != 0 and not isNaN d.ampl

#     plot.draw data
