const MainScreen = () => {
  return (
    <div className="screen-container">
      <div className="row">
        <div className="col">
          <button className="btn">Hello</button>

          <h1 className="text-3xl font-bold">Welcome to our Site</h1>

          <p>Primary landing area</p>
        </div>

        <div className="col">
          <button className="btn">World</button>
        </div>
      </div>

      <div className="row">
        <div className="col">
          <form name="MyForm">
            <label htmlFor="username">Username</label>

            <input
              type="text"
              name="username"
              placeholder="Username"
              required="True"
            />

            <label htmlFor="password">Password</label>

            <input
              type="password"
              name="password"
              placeholder="Password"
              required="True"
            />

            <input type="submit" />
          </form>
        </div>

        <div className="col">
          <img
            width="100%"
            height="100%"
            src="https://images.hdqwalls.com/wallpapers/mountain-scenery-morning-sun-rays-4k-kf.jpg"
          />
        </div>

        <div className="col">
          <div className="row"></div>

          <div className="row">
            <button className="btn">Button Hi!</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainScreen;
