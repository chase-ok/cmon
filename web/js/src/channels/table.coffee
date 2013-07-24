define ['utils', 'jquery', 'datatables', 'd3'], (utils, $, _, d3) ->
    webRoot = utils.definitions.webRoot
    class ChannelsTable
        constructor: (container) ->
            @container = $ container
            
            @columnIndex = ["ifo", "subsystem", "name", "excessPower", "omicron"]
            
            viewLink = (channel, source) =>
                "<a href=\"#{@triggersUrl channel, source}\">View</a>"
            @columns =
                ifo:
                    sTitle: "IFO"
                    sWidth: "10%"
                subsystem:
                    sTitle: "Subsystem"
                    sWidth: "30%"
                name:
                    sTitle: "Channel"
                    sWidth: "40%"
                excessPower:
                    sTitle: "Excess Power Triggers"
                    sClass: "center"
                    mRender: (channel, type, row) =>
                        if channel then viewLink channel, "excesspower" else "N/A"
                    sWidth: "10%"
                omicron:
                    sTitle: "Omicron Triggers"
                    sClass: "center"
                    mRender: (channel, type, row) ->
                        if channel then viewLink channel, "omicron" else "N/A"
                    sWidth: "10%"
            for name, def of @columns
                def.aTargets = [@columnIndex.indexOf name]
                
            @dataMap =
                ifo: (channel) -> channel.ifo
                subsystem: (channel) -> channel.subsystem
                name: (channel) -> channel.name
                excessPower: (channel) ->
                    value = channel.properties.trigger_source_excesspower
                    if value? and value then channel else false
                omicron: (channel) ->
                    value = channel.properties.trigger_source_omicron
                    if value? and value then channel else false
        
        triggersUrl: (channel, source) ->
            "#{webRoot}/triggers/#{channel.ifo}/#{channel.subsystem}/" +
            "#{channel.name}?source=#{source}"
        
        prepare: ->
            @table = $ "<table/>", 
                class: "dataTable"
                id: "channels"
                border: 0
                cellspacing: 0
                cellpadding: 0
            @table.appendTo @container
            
            @header = $ "<thead/>"
            @header.appendTo @table
            @headerRow = $ "<tr/>"
            @headerRow.appendTo @header
            
            for column, obj of @columns
                @headerRow.append $ "<th>#{obj.sTitle}</th>"
            
            @table = @table.dataTable
                aoColumns: (@columns[name] for name in @columnIndex)
            
        addChannel: (channel) ->
            row = (@dataMap[name] channel for name in @columnIndex)
            @table.fnAddData row
            
        loadFromUrl: (url="#{webRoot}/channels/all") ->
            d3.json url, (error, json) =>
                if error? or not json.success
                    console.log error
                    console.log json
                    return
                
                for channel in json.data.channels
                    @addChannel channel
    
    return {ChannelsTable}