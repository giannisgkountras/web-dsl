webpage MyHomePage
    Screen MainScreen
        title: "Welcome to Our Site"
        url: "/home"
        description: "Primary landing area"

        row
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
    end

    Screen ProfilePage
        title: "Your profile"
        url: "/profile"
        description: "Page to view user's profile"

        row
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