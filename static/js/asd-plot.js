// Generated by CoffeeScript 1.6.2
(function() {
  var Plot, console, d3, describe, height, line, margin, svg, width, x, xAxis, y, yAxis;

  d3 = this.d3;

  console = this.console;

  describe = function(obj, attrs) {
    var attr, value, _i, _len;

    for (value = _i = 0, _len = attrs.length; _i < _len; value = ++_i) {
      attr = attrs[value];
      obj.attr(attr, value);
    }
    return obj;
  };

  Plot = (function() {
    function Plot(dim) {
      this.dim = dim;
      this.margin = {
        top: 20,
        right: 20,
        bottom: 30,
        left: 50
      };
      this.plotDim = {
        x: this.dim.x - this.margin.left - this.margin.right,
        y: this.dim.y - this.margin.top - this.margin.bottom
      };
      this.setScale();
      this.domRoot = "body";
      this.prepared = false;
      this.showGrid = true;
    }

    Plot.prototype.logLog = function() {
      return setScale({
        x: "log",
        y: "log"
      });
    };

    Plot.prototype.semilogX = function() {
      return setScale({
        x: "log",
        y: "linear"
      });
    };

    Plot.prototype.semilogY = function() {
      return setScale({
        x: "linear",
        y: "log"
      });
    };

    Plot.prototype.setScale = function(type) {
      var _ref, _ref1;

      if (type == null) {
        type = {
          x: "linear",
          y: "linear"
        };
      }
      this.scaleType = {
        x: (_ref = type.x) != null ? _ref : this.scaleType.x,
        y: (_ref1 = type.y) != null ? _ref1 : this.scaleType.y
      };
      return this.scale = {
        x: d3.scale[xType]().clamp(true).range([0, this.plotDim.x]),
        y: d3.scale[yType]().clamp(true).range([this.plotDim.y, 0])
      };
    };

    Plot.prototype.setLimits = function(limits) {
      var _ref, _ref1;

      if (limits == null) {
        limits = {
          x: null,
          y: null
        };
      }
      this.limits = {
        x: (_ref = limits.x) != null ? _ref : d3.extent(this.data.x),
        y: (_ref1 = limits.y) != null ? _ref1 : d3.extent(this.data.y)
      };
      this.scale.x.domain(limits.x);
      return this.scale.y.domain(limits.y);
    };

    Plot.prototype.setAccessor = function(accessor) {
      var _ref, _ref1;

      if (accessor == null) {
        accessor = {
          x: null,
          y: null
        };
      }
      return this.accessor = {
        x: (_ref = accessor.x) != null ? _ref : this.accessor.x,
        y: (_ref1 = accessor.y) != null ? _ref1 : this.accessor.y
      };
    };

    Plot.prototype.makeAxis = function() {
      return {
        x: d3.svg.axis().scale(this.scale.x).orient("bottom"),
        y: d3.svg.axis().scale(this.scale.y).orient("left")
      };
    };

    Plot.prototype.makeLine = function() {
      this.line = d3.svg.line();
      if (this.accessor.x != null) {
        this.line.x(this.accessor.x);
      }
      if (this.accessor.y != null) {
        return this.line.y(this.accessor.y);
      }
    };

    Plot.prototype.makeCanvas = function() {
      var svg;

      svg = d3.select(this.domRoot).append("svg");
      describe(svg, {
        width: this.dim.x,
        height: this.dim.y
      });
      return this.canvas = describe(svg.append("g"), {
        transform: "translate({@margin.left}, {@margin.top})"
      });
    };

    Plot.prototype.prepare = function() {
      if (this.prepared) {
        return;
      }
      this.makeCanvas();
      this.makeLine();
      this.drawAxis();
      this.drawGrid();
      return this.prepared = true;
    };

    Plot.prototype.drawAxis = function() {
      var axis;

      axis = this.makeAxis();
      (describe(this.canvas.append("g")({
        "class": "x axis",
        transform: "translate(0, " + dim.y + ")"
      }))).call(axis.x);
      return (describe(this.canvas.append("g")({
        "class": "y axis"
      }))).call(axis.y);
    };

    Plot.prototype.drawGrid = function() {
      var axis;

      if (!this.showGrid) {
        return;
      }
      axis = this.makeAxis();
      axis.x.tickSize(-this.dim.y, 0, 0).tickFormat("");
      axis.y.tickSize(-this.dim.x, 0, 0).tickFormat("");
      (describe(this.canvas.append("g")({
        "class": "x grid",
        transform: "translate(0, " + this.dim.y + ")"
      }))).call(axis.x);
      return (describe(this.canvas.append("g")({
        "class": "y grid",
        transform: "translate(0, " + this.dim.y + ")"
      }))).call(axis.y);
    };

    Plot.prototype.draw = function(data) {
      this.data = data;
      this.prepare();
      return this.path = describe(this.canvas.append("path")({
        "class": "line",
        d: this.line(d)
      }));
    };

    return Plot;

  })();

  margin = {
    top: 20,
    right: 20,
    bottom: 30,
    left: 50
  };

  width = 900 - margin.left - margin.right;

  height = 600 - margin.top - margin.bottom;

  x = d3.scale.log().range([0, width]);

  y = d3.scale.log().clamp(true).range([height, 0]);

  xAxis = function() {
    return d3.svg.axis().scale(x).orient("bottom");
  };

  yAxis = function() {
    return d3.svg.axis().scale(y).orient("left");
  };

  line = d3.svg.line().x(function(d) {
    return x(d.date);
  }).y(function(d) {
    return y(d.close);
  });

  svg = d3.select("body").append("svg").attr("width", width + margin.left + margin.right).attr("height", height + margin.top + margin.bottom).append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  d3.json("asd/data", function(error, json) {
    var amplitude, clean, data, frequency, i, time;

    time = json.time, frequency = json.frequency, amplitude = json.amplitude;
    clean = function(x) {
      if (isNaN(+x)) {
        return 0.0;
      } else {
        return +x;
      }
    };
    data = (function() {
      var _i, _ref, _results;

      _results = [];
      for (i = _i = 0, _ref = frequency.length; 0 <= _ref ? _i <= _ref : _i >= _ref; i = 0 <= _ref ? ++_i : --_i) {
        _results.push({
          freq: clean(frequency[i]),
          ampl: clean(amplitude[i])
        });
      }
      return _results;
    })();
    x.domain([1, d3.max(frequency)]);
    y.domain([1e-24, d3.max(amplitude)]);
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis());
    svg.append("g").attr("class", "grid").attr("transform", "translate(0," + height + ")").call(xAxis().tickSize(-height, 0, 0).tickFormat(""));
    svg.append("text").attr("transform", "translate(" + (width / 2) + ", " + (height + margin.bottom) + ")").attr("text-anchor", "middle").attr("class", "x axis-label").text("Frequency [Hz]");
    svg.append("g").attr("class", "y axis").call(yAxis());
    svg.append("g").attr("transform", "rotate(-90)").append("text").attr("x", -height / 2).attr("y", 10 - margin.left).attr("text-anchor", "middle").attr("class", "y axis-label").text("Amplitude [Hz^-1/2]");
    svg.append("g").attr("class", "grid").call(yAxis().tickSize(-width, 0, 0).tickFormat(""));
    line = d3.svg.line().x(function(d) {
      return x(d.freq);
    }).y(function(d) {
      return y(d.ampl);
    }).defined(function(d) {
      return d.freq !== 0 && !isNaN(d.ampl);
    });
    return svg.append("path").attr("class", "line").attr("d", line(data));
  });

}).call(this);

/*
//@ sourceMappingURL=asd-plot.map
*/