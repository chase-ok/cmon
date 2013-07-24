define ['utils', 'd3'], (utils, d3) ->
    {definitions: defs, loadJSON, IntervalFunc} = utils
    _triggerCount = 0
    
    class Chunk
        constructor: (@startTime, @endTime) ->
            @accessedTime = 0
            @triggers = []
            @loaded = no
        
        load: (limit=1000) ->
            @accessedTime = new Date().getTime()
            return if @loaded
            
            url = "#{defs.webRoot}/triggers/#{defs.ifo}/#{defs.subsystem}/" +
                  "#{defs.channel}/#{@startTime}-#{@endTime}?" +
                  "source=#{defs.source}&limit=#{limit}"
            loadJSON url, (data) =>
                @triggers = data.triggers
                for trigger in @triggers
                    trigger.id = _triggerCount += 1
                @loaded = yes  
        
    class TriggerStore
        constructor: (@timeChunk=30, @maxChunks=50)->
            @chunks = {}
            @_garbageCollecting = new IntervalFunc @garbageCollect, 10000
        
        garbageCollecting: (garbageCollecting, period=10000) ->
            if garbageCollecting?
                @_garbageCollecting.period period
                @_garbageCollecting.running garbageCollecting
                this
            else
                @_garbageCollecting.running()
            
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
    
    return {Chunk, TriggerStore}
