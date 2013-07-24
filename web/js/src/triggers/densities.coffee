define ['utils', 'plots', 'd3', 'jquery'], (utils, plots, d3, $) ->
    {definitions: defs, describe, loadJSON} = utils
    
    toDate = (seconds) -> new Date(seconds*1000)
    
    class DensityPlot extends plots.ZColorPlot
        constructor: (rootSelector) ->
            super rootSelector
            
            @_scroller = null
            @axisLabels
                x: "Time [s]"
                y: "Frequency [Hz]"
                z: "SNR Density"
            @scales
                x: d3.time.scale()
                y: d3.scale.log().clamp yes
                z: d3.scale.log().clamp yes
            @ticks
                x: [5]
                y: [5]
                z: [5]
            
        scroller: (scroller) ->
            if scroller? 
                @_scroller = scroller
                this
            else 
                @_scroller
                
        load: ->
            url = "#{defs.webRoot}/triggers/#{defs.ifo}/#{defs.subsystem}/" +
                  "#{defs.channel}/densities?source=#{defs.source}"
            loadJSON url, (data) =>
                {times, frequencies, densities} = data
                
                # Add an upper limit to the bins
                highestFreq = frequencies[frequencies.length-1]
                frequencies.push 2*highestFreq
                # Add an upper limit to times
                times.push 2*times[times.length-1] - times[times.length-2]
                
                data = @_makeData times, frequencies, densities
                @_draw times, frequencies, data
        
        _makeData: (times, frequencies, densities) ->            
            data = []
            for row in [0...densities.length]
                [start, end] = times[row..row+1]
                continue if start is 0 or end is 0
                [startDate, endDate] = [start, end].map toDate
                
                densityRow = densities[row]
                for column in [0...densityRow.length]
                    density = densityRow[column]
                    continue if density < 1e1
                    
                    data.push
                        startDate: startDate
                        endDate: endDate
                        freqMin: frequencies[column]
                        freqMax: frequencies[column+1]
                        density: density
            return data
            
        _draw: (times, frequencies, data) ->
            @prepare()
            
            @limits
                x: [times[0], times[times.length-1]].map toDate
                y: d3.extent frequencies
                z: [1e1, 1e10]
            maps = @maps()
            
            # We're going to render to an image to save on memory
            rootElem = $ @root[0][0]
            offset = 
                x: rootElem.position().left + @margin.left
                y: rootElem.position().top + @margin.top
            image = describe $("<canvas/>"),
                id: 'density-image'
                width: @canvasSize.x
                height: @canvasSize.y
            image.css
                position: "absolute"
                left: offset.x
                top: offset.y
            image.appendTo $ 'body'
            context = image[0].getContext "2d"
            
            for d in data
                context.fillStyle = maps.z d.density
                
                x = Math.round maps.x d.startDate
                y = Math.round maps.y d.freqMax
                width = Math.ceil maps.x(d.endDate) - maps.x(d.startDate)
                height = Math.ceil maps.y(d.freqMin) - maps.y(d.freqMax)
                context.fillRect x, y, width, height
            
            image.click (event) =>
                x = event.pageX - offset.x
                time = Math.round @scales().x.invert(x)/1000
                @_scroller.scrollTo time, 0 if @_scroller?
            
            #brush = d3.svg.brush().x(@scales().x)
            #brush.on "brushstart", => console.log "STARTING"
            #brush.on "brushend", => console.log "ENDING"
            #brush.on "brush", =>
                #console.log "BRUSHING"
                #time = brush.extent()[0]
                #brush.extent [time, time+1]
                #@_scroller.scrollTo time, 0 if @_scroller?
            #brush @canvas
            #console.log brush
    
    return {DensityPlot}