
d3 = @d3
console = @console

describe = (obj, attrs) ->
    for attr, value in attrs
        obj.attr attr, value
    obj

class Plot
    constructor: (@dim) ->
        @margin = {top: 20, right: 20, bottom: 30, left: 50}
        @plotDim = 
            x: @dim.x - @margin.left - @margin.right
            y: @dim.y - @margin.top - @margin.bottom
        @setScale()
        @domRoot = "body"
        @prepared = false
        @showGrid = true

    logLog: -> setScale({x: "log", y: "log"})
    semilogX: -> setScale({x: "log", y: "linear"})
    semilogY: -> setScale({x: "linear", y: "log"})

    setScale: (type={x:"linear", y:"linear"}) ->
        @scaleType = 
            x: type.x ? @scaleType.x
            y: type.y ? @scaleType.y
        @scale = 
            x: d3.scale[xType]().clamp(yes).range [0, @plotDim.x]
            y: d3.scale[yType]().clamp(yes).range [@plotDim.y, 0]

    setLimits: (limits={x: null, y: null}) ->
        @limits =
            x: limits.x ? d3.extent @data.x
            y: limits.y ? d3.extent @data.y
        @scale.x.domain limits.x
        @scale.y.domain limits.y

    setAccessor: (accessor={x: null, y: null}) ->
        @accessor = {x: accessor.x ? @accessor.x, y: accessor.y ? @accessor.y}

    makeAxis: ->
        x: d3.svg.axis().scale(@scale.x).orient("bottom")
        y: d3.svg.axis().scale(@scale.y).orient("left")

    makeLine: ->
        @line = d3.svg.line()
        @line.x(@accessor.x) if @accessor.x?
        @line.y(@accessor.y) if @accessor.y?

    makeCanvas: ->
        svg = d3.select(@domRoot).append("svg")
        describe svg,
            width: @dim.x
            height: @dim.y
        @canvas = describe svg.append("g"),
            transform: "translate({@margin.left}, {@margin.top})"

    prepare: ->
        return if @prepared

        @makeCanvas()
        @makeLine()
        @drawAxis()
        @drawGrid()

        @prepared = true

    drawAxis: ->
        axis = @makeAxis()
        (describe @canvas.append("g")
            class: "x axis"
            transform: "translate(0, #{dim.y})"
        ).call(axis.x)
        (describe @canvas.append("g")
            class: "y axis"
        ).call(axis.y)

    drawGrid: ->
        return unless @showGrid

        axis = @makeAxis()
        axis.x.tickSize(-@dim.y, 0, 0).tickFormat("")
        axis.y.tickSize(-@dim.x, 0, 0).tickFormat("")
        
        (describe @canvas.append("g")
            class: "x grid"
            transform: "translate(0, #{@dim.y})"
        ).call(axis.x)
        (describe @canvas.append("g")
            class: "y grid"
            transform: "translate(0, #{@dim.y})"
        ).call(axis.y)

    draw: (data) ->
        @data = data 
        @prepare()

        @path = describe @canvas.append("path")
            class: "line"
            d: @line d


margin = {top: 20, right: 20, bottom: 30, left: 50}
width = 900 - margin.left - margin.right
height = 600 - margin.top - margin.bottom

x = d3.scale.log().range [0, width]
y = d3.scale.log().clamp(yes).range [height, 0]


xAxis = -> d3.svg.axis().scale(x).orient("bottom")
yAxis = -> d3.svg.axis().scale(y).orient("left")

line = d3.svg.line()
       .x((d) -> x d.date)
       .y((d) -> y d.close)

svg = d3.select("body").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

d3.json "asd/data", (error, json) ->
  {time, frequency, amplitude} = json

  clean = (x) -> if isNaN(+x) then 0.0 else +x
  data = ({freq: clean(frequency[i]), ampl: clean(amplitude[i])}\
          for i in [0..frequency.length])

  x.domain [1, d3.max(frequency)] # avoid a 0 here
  y.domain [1e-24, d3.max(amplitude)]

  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis())
  svg.append("g")
      .attr("class", "grid")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis().tickSize(-height, 0, 0).tickFormat(""))
  svg.append("text")
      .attr("transform", "translate(#{width/2}, #{height + margin.bottom})")
      .attr("text-anchor", "middle")
      .attr("class", "x axis-label")
      .text("Frequency [Hz]")

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis())
  svg.append("g")
      .attr("transform", "rotate(-90)")
    .append("text")
      .attr("x", -height/2)
      .attr("y", 10-margin.left)
      .attr("text-anchor", "middle")
      .attr("class", "y axis-label")
      .text("Amplitude [Hz^-1/2]")
  svg.append("g")
      .attr("class", "grid")
      .call(yAxis().tickSize(-width, 0, 0).tickFormat(""))

  line = d3.svg.line()\
         .x((d) -> x d.freq)
         .y((d) -> y d.ampl)
         .defined((d) -> d.freq != 0 and !isNaN(d.ampl))
  
  svg.append("path")
      .attr("class", "line")
      .attr("d", line data)
