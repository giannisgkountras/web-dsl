import { useState } from "react";
import ObjectEditor from "./ObjectEditor";
import { IoSend } from "react-icons/io5";
import { publish } from "../api/publish";

const Publish = ({ brokerName }) => {
    const [dataToPublish, setDataToPublish] = useState({ key: "value" });
    const [topic, setTopic] = useState("");
    const [jsonError, setJsonError] = useState(null);

    return (
        <div className="flex justify-center items-center flex-col w-full">
            <h1 className="font-bold">{brokerName}</h1>
            <p>Enter the topic:</p>
            <input
                type="text"
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Topic"
            />
            <ObjectEditor
                initialData={dataToPublish}
                onChange={setDataToPublish}
                jsonError={jsonError}
                setJsonError={setJsonError}
            />
            <button
                className="btn text-[#fff] flex cursor-pointer items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => publish(brokerName, topic, dataToPublish)}
                disabled={!!jsonError || topic === ""} // Disable when JSON is invalid or topic is empty
            >
                Publish Message <IoSend className="ml-2" />
            </button>
        </div>
    );
};

export default Publish;
