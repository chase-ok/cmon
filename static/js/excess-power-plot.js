// Generated by CoffeeScript 1.6.3
(function() {
  var BurstPlot, channel, console, d3, describe, ifo, isEmpty, lastGPSTime, lastLocalTime, mergeObj, plot, refreshTime, root, startGPSTime, startLocalTime, subsystem, timerStarted, updateBursts, updateTime;

  d3 = this.d3;

  console = this.console;

  ifo = this.ifo;

  subsystem = this.subsystem;

  channel = this.channel;

  startGPSTime = this.startTime;

  startLocalTime = new Date().getTime() / 1000;

  root = this.root;

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

  BurstPlot = (function() {
    function BurstPlot(rootSelector) {
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

    BurstPlot.prototype.select = function(selector) {
      return d3.select("" + this.rootSelector + " " + selector);
    };

    BurstPlot.prototype.setScale = function(type) {
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
        x: d3.scale[this.scaleType.x]().clamp(false).range([0, this.plotDim.x]),
        y: d3.scale[this.scaleType.y]().clamp(true).range([this.plotDim.y, 0]),
        z: d3.scale[this.scaleType.z]().clamp(true).range([this.plotDim.y, 0])
      };
      if (alreadySet) {
        this.setLimits();
      }
      return this.refresh();
    };

    BurstPlot.prototype.setLimits = function(limits) {
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

    BurstPlot.prototype.setAxisLabel = function(label) {
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

    BurstPlot.prototype.setTicks = function(format) {
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

    BurstPlot.prototype.setZColor = function(colors) {
      if (colors == null) {
        colors = {
          lower: null,
          upper: null
        };
      }
      this.zColor = mergeObj(this.zColor, colors);
      return this.refresh();
    };

    BurstPlot.prototype.makeAxis = function() {
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

    BurstPlot.prototype.makeCanvas = function() {
      this.canvas = describe(this.root.append("g"), {
        transform: "translate(" + this.margin.left + ", " + this.margin.top + ")"
      });
      return this.defs = this.canvas.append("defs");
    };

    BurstPlot.prototype.makeZColorMap = function() {
      var colorInterp, height, map;
      map = this.scale.z;
      height = this.plotDim.y;
      colorInterp = d3.interpolateRgb(this.zColor.lower, this.zColor.upper);
      return function(z) {
        return colorInterp(1.0 - map(z) / height);
      };
    };

    BurstPlot.prototype.makeZGradient = function() {
      this.zGradient = describe(this.defs.append("linearGradient"), {
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

    BurstPlot.prototype.makePlotClipPath = function() {
      this.plotClipId = "plotClip";
      this.plotClip = this.canvas.append("clipPath").attr("id", this.plotClipId);
      return describe(this.plotClip.append("rect"), {
        x: 0,
        y: 0,
        width: this.plotDim.x,
        height: this.plotDim.y
      });
    };

    BurstPlot.prototype.prepare = function() {
      if (this.prepared) {
        return;
      }
      this.makeCanvas();
      this.makeZGradient();
      this.makePlotClipPath();
      this.drawGrid();
      this.drawAxis();
      this.drawAxisLabels();
      this.drawZColorBar();
      return this.prepared = true;
    };

    BurstPlot.prototype.drawAxis = function() {
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

    BurstPlot.prototype.drawGrid = function() {
      var axis;
      if (!this.showGrid) {
        return;
      }
      axis = this.makeAxis();
      axis.x.tickSize(-this.plotDim.y, 0, 0).tickFormat("");
      axis.y.tickSize(-this.plotDim.x, 0, 0).tickFormat("");
      (describe(this.canvas.append("g"), {
        "class": "x grid",
        transform: "translate(0, " + this.plotDim.y + ")"
      })).call(axis.x);
      return (describe(this.canvas.append("g"), {
        "class": "y grid"
      })).call(axis.y);
    };

    BurstPlot.prototype.drawAxisLabels = function() {
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

    BurstPlot.prototype.drawZColorBar = function() {
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

    BurstPlot.prototype.draw = function(gpsTime, bursts) {
      var burst, fCenter, fMax, fMin, getHeight, getWidth, halfBand, mapTime, mapX, mapY, mapZ, rect, totalBandwidth, totalTime, x0, _i, _len, _ref, _ref1,
        _this = this;
      this.prepare();
      totalTime = Math.abs(this.limits.x[0] - this.limits.x[1]);
      totalBandwidth = Math.abs(this.limits.y[0] - this.limits.y[1]);
      _ref = this.scale, mapX = _ref.x, mapY = _ref.y;
      mapZ = this.makeZColorMap();
      mapTime = function(seconds, ns) {
        return mapX(seconds + ns * 1e-9 - gpsTime);
      };
      getWidth = function(duration) {
        return Math.ceil(_this.plotDim.x * (duration / totalTime));
      };
      getHeight = function(fMin, fMax) {
        return Math.abs(mapY(fMax) - mapY(fMin));
      };
      for (_i = 0, _len = bursts.length; _i < _len; _i++) {
        burst = bursts[_i];
        x0 = mapTime(burst.start_time, burst.start_time_ns);
        halfBand = burst.bandwidth / 2;
        fCenter = burst.central_freq;
        _ref1 = [fCenter - halfBand, fCenter + halfBand], fMin = _ref1[0], fMax = _ref1[1];
        rect = this.canvas.insert("rect");
        rect.datum(burst);
        describe(rect, {
          "class": "value",
          x: x0,
          y: mapY(fMax),
          width: getWidth(burst.duration),
          height: getHeight(fMin, fMax),
          stroke: "none",
          opacity: "1.0",
          fill: mapZ(burst.confidence),
          "clip-path": "url(#" + this.plotClipId + ")"
        });
        rect.style("shape-rendering", "crispEdges");
        rect.transition().duration(1000 * (totalTime + burst.start_time + burst.start_time_ns * 1e-9 - gpsTime + burst.duration)).ease("linear").attr("x", -getWidth(burst.duration)).each("end", function() {
          return d3.select(this).remove();
        });
      }
      return this.drawn = true;
    };

    BurstPlot.prototype.refresh = function() {
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

    return BurstPlot;

  })();

  plot = new BurstPlot("#plot");

  plot.setScale({
    z: "log"
  });

  plot.setAxisLabel({
    x: "Time [s]",
    y: "Frequency [Hz]",
    z: "Confidence",
    title: "Excess Power Bursts"
  });

  plot.setLimits({
    y: [1, 5000],
    x: [-30, 0],
    z: [10, 30]
  });

  lastGPSTime = Math.floor(startGPSTime);

  lastLocalTime = startLocalTime;

  refreshTime = 5000;

  timerStarted = false;

  updateTime = function() {
    var gpsTime;
    timerStarted = true;
    gpsTime = startGPSTime + (new Date().getTime() / 1000 - startLocalTime);
    plot.setAxisLabel({
      x: "Time [s] since " + (Math.round(gpsTime))
    });
    return setTimeout(updateTime, 1000);
  };

  updateBursts = function() {
    var newGPSTime, newLocalTime;
    newLocalTime = new Date().getTime() / 1000;
    newGPSTime = lastGPSTime + (newLocalTime - lastLocalTime);
    console.log("" + root + "/excesspower/" + subsystem + "/" + channel + "/bursts/" + (Math.floor(lastGPSTime)) + "-" + (Math.floor(newGPSTime)));
    return d3.json("" + root + "/excesspower/" + subsystem + "/" + channel + "/bursts/" + (Math.floor(lastGPSTime)) + "-" + (Math.floor(newGPSTime)) + "?limit=100", function(error, json) {
      var bursts;
      if ((error != null) || !json.success) {
        if (error != null) {
          console.log(error);
        }
        if (json != null) {
          console.log(json.error);
        }
        setTimeout(updateBursts, refreshTime);
        return;
      }
      bursts = json.data.bursts;
      console.log("TIME " + lastGPSTime);
      console.log("#Bursts " + bursts.length);
      plot.draw(lastGPSTime, bursts);
      lastGPSTime = newGPSTime;
      lastLocalTime = newLocalTime;
      setTimeout(updateBursts, refreshTime);
      if (!timerStarted) {
        return updateTime();
      }
    });
  };

  updateBursts();

}).call(this);
