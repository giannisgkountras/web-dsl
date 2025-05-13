import { useState, useContext, useEffect, Fragment, use } from "react";
import { evaluateComplexCondition } from "../utils/evaluateCondition";

const Condition = ({
    allDataNeededFromEntities,
    condition,
    elements,
    elementsElse = <></>
}) => {
    const [showComponent, setShowComponent] = useState(false);

    useEffect(() => {
        if (allDataNeededFromEntities) {
            setShowComponent(
                evaluateComplexCondition(condition, allDataNeededFromEntities)
            );
        }
    }, [allDataNeededFromEntities]);

    return showComponent
        ? elements.map((el, idx) => <Fragment key={idx}>{el}</Fragment>)
        : elementsElse.map((el, idx) => <Fragment key={idx}>{el}</Fragment>);
};

export default Condition;
