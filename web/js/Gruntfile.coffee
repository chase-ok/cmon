module.exports = (grunt) ->
    src = 'src'
    lib = 'lib'
    dst = '../../static/js'
    
    grunt.initConfig
        pkg: grunt.file.readJSON 'package.json'
        uglify:
            options:
                banner: '/*! <%= pkg.name %> <%= grunt.template.today("yyyy-mm-dd") %> */\n'
            build:
                src: 'src/<%= pkg.name %>.js'
                dest: 'build/<%= pkg.name %>.min.js'
        
        coffee:
            triggers:
                expand: true
                flatten: true
                cwd: "#{src}/triggers"
                src: '*.coffee'
                dest: "#{dst}/triggers"
                ext: '.js'
            'triggers-main':
                src: ["#{src}/libraries.coffee", "#{src}/triggers.coffee"]
                dest: "#{dst}/triggers.js"
                
            channels:
                expand: true
                flatten: true
                cwd: "#{src}/channels"
                src: '*.coffee'
                dest: "#{dst}/channels"
                ext: '.js'
            'channels-main':
                src: ["#{src}/libraries.coffee", "#{src}/channels.coffee"]
                dest: "#{dst}/channels.js"
            
            plots:
                src: "#{src}/plots.coffee"
                dest: "#{dst}/plots.js"
            utils:
                src: "#{src}/utils.coffee"
                dest: "#{dst}/utils.js"
    
        copy:
            libraries:
                files: [
                    {expand: true, src: ["#{lib}/*"], dest: "#{dst}", filter: 'isFile'}
                ]

    grunt.loadNpmTasks 'grunt-contrib-uglify'
    grunt.loadNpmTasks 'grunt-contrib-coffee'
    grunt.loadNpmTasks 'grunt-contrib-copy'
    
    grunt.registerTask 'default', ['coffee']