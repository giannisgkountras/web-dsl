webpage MyCoolWebsite
    Screen MainScreen
        title: "Welcome to Our Site"
        url: "/"
        description: "Primary landing area"

        row
            col
                Button TestBTN
                    text: "Hello"
            endcol
            col
                Button WorldBTN
                text: "World"
            endcol
        endrow
        row
            col
                Form MyForm
                    Label username
                        content: "Username"
                    Input username
                        type: "text"
                        placeholder: "Username"
                        required: true
                    Label password
                        content: "Password"
                    Input password
                        type: "password"
                        placeholder: "Password"
                        required: true
                endform
            endcol
            col
                Image TestImg
                    source:"https://images.hdqwalls.com/wallpapers/mountain-scenery-morning-sun-rays-4k-kf.jpg"
            endcol
            col
                row
                endrow
                row
                    Button NestedBtn
                    text: "Button Hi!"
                endrow
            endcol
        endrow
    end

    Screen ComplexLayout
        title: "Complex Layout"
        url: "/complex"
        description: "A more complex layout screen"

        row
            col
            endcol
            col
                row
                endrow               
                row
                    col
                        row
                        endrow
                        row
                        endrow
                        row
                        endrow
                    endcol
                    col
                    endcol
                endrow
                row
                endrow
            endcol
        endrow
        row
            col
                row
                endrow
                row
                    col
                    endcol
                    col
                    endcol
                    col
                    endcol
                    col
                    endcol
                    col
                    endcol                    
                    col
                    endcol                    
                    col
                    endcol
                endrow
                row
                endrow
                row
                endrow
            endcol
            col
            endcol
            col
            endcol
            col
            endcol
            col
            endcol
            col
            endcol
        endrow
    end

    Screen Dashboard
        title: "Main Dashboard"
        url: "/dashboard"
        description: "The dashboard of the application"

        row
            col
            endcol
            col
            endcol
            col
            endcol
        endrow
        row
            col
            endcol
            col
            endcol
            col
            endcol
        endrow
        row
            col
            endcol
            col
            endcol
            col
            endcol
        endrow
    end