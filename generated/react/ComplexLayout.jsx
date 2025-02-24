const ComplexLayout = () => {
  return (
    <>
      <h1>Complex Layout</h1>

      <p>A more complex layout screen</p>

      <div className="row">
        <div className="col"></div>

        <div className="col">
          <div className="row"></div>

          <div className="row">
            <div className="col">
              <div className="row"></div>

              <div className="row"></div>

              <div className="row"></div>
            </div>

            <div className="col"></div>
          </div>

          <div className="row"></div>
        </div>
      </div>

      <div className="row">
        <div className="col">
          <div className="row"></div>

          <div className="row">
            <div className="col"></div>

            <div className="col"></div>

            <div className="col"></div>

            <div className="col"></div>

            <div className="col"></div>

            <div className="col"></div>

            <div className="col"></div>
          </div>

          <div className="row"></div>

          <div className="row"></div>
        </div>

        <div className="col"></div>

        <div className="col"></div>

        <div className="col"></div>

        <div className="col"></div>

        <div className="col"></div>
      </div>
    </>
  );
};

export default ComplexLayout;
