webpage MyCoolWebsite
    author: "Giannis"
    version: "1.0.0"
    description: "My very cool website"
    navbar: true
Screen MainScreen
    title: "Welcome to Our Site"
    url: "/"
    description: "Primary landing area"

    row
        col
            h1 "Welcome to our Site"
            p "Primary landing area"
            Button "Hello"
        endcol
        col
            h2 "Hello to the"
            Button "World"
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
                Button "Button Hi!"
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

Screen Games
    title: "Games"
    url: "/games"

    col
        h1 "This is the games screen"
        h2 "This is the games screen"
        p "This is the games screen"
        Button "Games Button"
    endcol
end