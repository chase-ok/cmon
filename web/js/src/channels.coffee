
define ['jquery', 'channels/table'], ($, table) ->
    $ ->
        table = new table.ChannelsTable $ "#container"
        table.prepare()
        table.loadFromUrl()