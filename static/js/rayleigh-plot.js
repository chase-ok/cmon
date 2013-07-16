// Generated by CoffeeScript 1.6.3
(function() {
  var MatrixPlot, console, d3, describe, isEmpty, mergeObj, plot, refreshTime, updateLatestBlock;

  d3 = this.d3;

  console = this.console;

  describe = function(obj, attrs) {
    var attr, value;
    for (attr in attrs) {
      value = attrs[attr];
      obj = obj.attr(attr, value);
    }
    return obj;
  };

  mergeObj = function(base, newObj) {
    var key, value;
    if (base == null) {
      base = {};
    }
    for (key in newObj) {
      value = newObj[key];
      if (value != null) {
        base[key] = value;
      }
    }
    return base;
  };

  isEmpty = function(obj) {
    var prop, value;
    for (prop in obj) {
      value = obj[prop];
      if (obj.hasOwnProperty(prop)) {
        return false;
      }
    }
    return true;
  };

  MatrixPlot = (function() {
    function MatrixPlot(rootSelector) {
      this.rootSelector = rootSelector != null ? rootSelector : "body";
      this.root = d3.select(this.rootSelector);
      this.dim = {
        x: this.root.attr("width"),
        y: this.root.attr("height")
      };
      this.margin = {
        top: 20,
        right: 50,
        bottom: 40,
        left: 50
      };
      this.zBarWidth = 30;
      this.plotDim = {
        x: this.dim.x - this.margin.left - this.margin.right - this.zBarWidth,
        y: this.dim.y - this.margin.top - this.margin.bottom
      };
      this.setScale();
      this.setTicks();
      this.setAxisLabel({
        x: "x",
        y: "y",
        z: "z",
        title: ""
      });
      this.setZColor({
        lower: d3.rgb("black"),
        upper: d3.rgb(255, 0, 0)
      });
      this.prepared = false;
      this.drawn = false;
      this.showGrid = true;
    }

    MatrixPlot.prototype.select = function(selector) {
      return d3.select("" + this.rootSelector + " " + selector);
    };

    MatrixPlot.prototype.setScale = function(type) {
      var alreadySet;
      if (type == null) {
        type = {
          x: "linear",
          y: "linear",
          z: "linear"
        };
      }
      this.scaleType = mergeObj(this.scaleType, type);
      alreadySet = this.scale != null;
      this.scale = {
        x: d3.scale[this.scaleType.x]().clamp(true).range([0, this.plotDim.x]),
        y: d3.scale[this.scaleType.y]().clamp(true).range([this.plotDim.y, 0]),
        z: d3.scale[this.scaleType.z]().clamp(true).range([this.plotDim.y, 0])
      };
      if (alreadySet) {
        this.setLimits();
      }
      return this.refresh();
    };

    MatrixPlot.prototype.setLimits = function(limits) {
      if (limits == null) {
        limits = {
          x: null,
          y: null,
          z: null
        };
      }
      this.limits = mergeObj(this.limits, limits);
      if (this.limits.x != null) {
        this.scale.x.domain(this.limits.x);
      }
      if (this.limits.y != null) {
        this.scale.y.domain(this.limits.y);
      }
      if (this.limits.z != null) {
        this.scale.z.domain(this.limits.z);
      }
      return this.refresh();
    };

    MatrixPlot.prototype.setAxisLabel = function(label) {
      if (label == null) {
        label = {
          x: null,
          y: null,
          z: null,
          title: null
        };
      }
      this.label = mergeObj(this.label, label);
      if (this.prepared) {
        this.select(".title.axis-label").text(this.label.title);
        this.select(".x.axis-label").text(this.label.x);
        this.select(".y.axis-label").text(this.label.y);
        return this.select(".z.axis-label").text(this.label.z);
      }
    };

    MatrixPlot.prototype.setTicks = function(format) {
      if (format == null) {
        format = {
          x: null,
          y: null,
          z: null
        };
      }
      this.ticks = mergeObj(this.ticks, format);
      return this.refresh();
    };

    MatrixPlot.prototype.setZColor = function(colors) {
      if (colors == null) {
        colors = {
          lower: null,
          upper: null
        };
      }
      this.zColor = mergeObj(this.zColor, colors);
      return this.refresh();
    };

    MatrixPlot.prototype.makeAxis = function() {
      var make;
      make = function(orient, type, ticks) {
        var axis;
        axis = d3.svg.axis().scale(type).orient(orient);
        if (ticks != null) {
          axis.ticks.apply(axis, ticks);
        }
        return axis;
      };
      return {
        x: make("bottom", this.scale.x, this.ticks.x),
        y: make("left", this.scale.y, this.ticks.y),
        z: make("right", this.scale.z, this.ticks.z)
      };
    };

    MatrixPlot.prototype.makeCanvas = function() {
      return this.canvas = describe(this.root.append("g"), {
        transform: "translate(" + this.margin.left + ", " + this.margin.top + ")"
      });
    };

    MatrixPlot.prototype.makeZColorMap = function() {
      var colorInterp, height, map;
      map = this.scale.z;
      height = this.plotDim.y;
      colorInterp = d3.interpolateRgb(this.zColor.lower, this.zColor.upper);
      return function(z) {
        return colorInterp(1.0 - map(z) / height);
      };
    };

    MatrixPlot.prototype.makeZGradient = function() {
      this.zGradient = describe(this.canvas.append("defs").append("linearGradient"), {
        id: "zGradient",
        x1: "0%",
        y1: "100%",
        x2: "0%",
        y2: "0%"
      });
      this.zGradientStart = describe(this.zGradient.append("stop"), {
        offset: "0%",
        "stop-color": this.zColor.lower,
        "stop-opacity": 1
      });
      return this.zGradientStop = describe(this.zGradient.append("stop"), {
        offset: "100%",
        "stop-color": this.zColor.upper,
        "stop-opacity": 1
      });
    };

    MatrixPlot.prototype.prepare = function() {
      if (this.prepared) {
        return;
      }
      this.makeCanvas();
      this.makeZGradient();
      this.drawAxis();
      this.drawAxisLabels();
      this.drawZColorBar();
      return this.prepared = true;
    };

    MatrixPlot.prototype.drawAxis = function() {
      var axis;
      axis = this.makeAxis();
      (describe(this.canvas.append("g"), {
        "class": "x axis",
        transform: "translate(0, " + this.plotDim.y + ")"
      })).call(axis.x);
      (describe(this.canvas.append("g"), {
        "class": "y axis"
      })).call(axis.y);
      return (describe(this.canvas.append("g"), {
        "class": "z axis",
        transform: "translate(" + (this.plotDim.x + this.zBarWidth) + ", 0)"
      })).call(axis.z);
    };

    MatrixPlot.prototype.drawAxisLabels = function() {
      var rotated;
      describe(this.canvas.append("text").text(this.label.title), {
        x: this.plotDim.x / 2,
        y: -this.margin.top + 10,
        "text-anchor": "middle",
        "class": "title axis-label"
      });
      describe(this.canvas.append("text").text(this.label.x), {
        x: this.plotDim.x / 2,
        y: this.plotDim.y + this.margin.bottom - 5,
        "text-anchor": "middle",
        "class": "x axis-label"
      });
      rotated = this.canvas.append("g").attr("transform", "rotate(-90)");
      describe(rotated.append("text").text(this.label.y), {
        x: -this.plotDim.y / 2,
        y: 10 - this.margin.left,
        "text-anchor": "middle",
        "class": "y axis-label"
      });
      return describe(rotated.append("text").text(this.label.z), {
        x: -this.plotDim.y / 2,
        y: this.plotDim.x + this.zBarWidth + this.margin.right,
        "text-anchor": "middle",
        "class": "z axis-label"
      });
    };

    MatrixPlot.prototype.drawZColorBar = function() {
      var spacing;
      spacing = 10;
      return describe(this.canvas.append("rect"), {
        x: this.plotDim.x + spacing,
        y: 0,
        width: this.zBarWidth - spacing,
        height: this.plotDim.y,
        fill: "url(#zGradient)"
      });
    };

    MatrixPlot.prototype.draw = function(x, y, z) {
      var col, data, height, mapX, mapY, mapZ, rects, row, width, _i, _j, _ref, _ref1, _ref2;
      this.prepare();
      data = [];
      for (row = _i = 0, _ref = y.length; 0 <= _ref ? _i < _ref : _i > _ref; row = 0 <= _ref ? ++_i : --_i) {
        for (col = _j = 0, _ref1 = x.length; 0 <= _ref1 ? _j < _ref1 : _j > _ref1; col = 0 <= _ref1 ? ++_j : --_j) {
          data.push([x[col], y[row], z[row][col]]);
        }
      }
      _ref2 = this.scale, mapX = _ref2.x, mapY = _ref2.y;
      mapZ = this.makeZColorMap();
      width = Math.round(this.plotDim.x / x.length);
      height = Math.round(this.plotDim.y / y.length);
      rects = this.canvas.selectAll("rect#value").data(data);
      describe(rects.enter().insert("rect"), {
        "class": "value",
        x: function(d) {
          return Math.round(mapX(d[0]));
        },
        y: function(d) {
          return Math.round(mapY(d[1]) - height);
        },
        width: width,
        height: height,
        stroke: "none",
        fill: function(d) {
          return mapZ(d[2]);
        }
      });
      rects.transition().duration(1000).attr("fill", function(d) {
        return mapZ(d[2]);
      });
      return this.drawn = true;
    };

    MatrixPlot.prototype.refresh = function() {
      if (!this.prepared) {
        return;
      }
      this.canvas.remove();
      this.prepared = false;
      this.drawn = false;
      this.prepare();
      if (this.drawn) {
        return this.draw(this.data);
      }
    };

    return MatrixPlot;

  })();

  plot = new MatrixPlot("#plot");

  plot.setAxisLabel({
    x: "Frequency [Hz]",
    y: "Time [s]",
    z: "STD/Mean",
    title: "Rayleigh Statistic"
  });

  plot.setLimits({
    y: [0, 60],
    x: [0, 8192],
    z: [0, 2]
  });

  refreshTime = 10000;

  updateLatestBlock = function() {
    return d3.json("rayleigh/blocks/latest?num_frequency_bins=60", function(error, json) {
      var frequencies, rs, start_time, time_offsets, _ref;
      if ((error != null) || !json.success) {
        if (error != null) {
          console.log(error);
        }
        if (json != null) {
          console.log(json.error);
        }
        setTimeout(updateLatestBlock, refreshTime);
        return;
      }
      _ref = json.data, start_time = _ref.start_time, time_offsets = _ref.time_offsets, frequencies = _ref.frequencies, rs = _ref.rs;
      plot.setAxisLabel({
        y: "Time [s] since " + start_time
      });
      plot.setLimits({
        z: d3.extent(d3.merge(rs))
      });
      plot.draw(frequencies, time_offsets, rs);
      return setTimeout(updateLatestBlock, refreshTime);
    });
  };

  updateLatestBlock();

}).call(this);
