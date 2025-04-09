import { useEffect, useState } from "react";
import ObjectEditor from "./ObjectEditor";
import { IoSend } from "react-icons/io5";
import { publish } from "../api/publish";

const Publish = ({ brokerName, destinationTopic = null, json = null }) => {
    const [dataToPublish, setDataToPublish] = useState({ key: "value" });
    const [topic, setTopic] = useState("");
    const [jsonError, setJsonError] = useState(null);

    useEffect(() => {
        if (destinationTopic) {
            setTopic(destinationTopic);
        }
        if (json) {
            setDataToPublish(json);
        }
    }, []);

    return (
        <>
            {!destinationTopic && !json ? (
                <div className="flex justify-center items-center flex-col w-full ">
                    <h1 className="mb-2 text-lg font-semibold text-gray-200">
                        {brokerName}
                    </h1>
                    <h2 className="mb-2 text-lg font-semibold text-gray-200 text-start w-11/12">
                        Edit Topic
                    </h2>
                    <input
                        type="text"
                        onChange={(e) => setTopic(e.target.value)}
                        className="w-11/12 p-2 rounded-md mb-4"
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
                        onClick={() =>
                            publish(brokerName, topic, dataToPublish)
                        }
                        disabled={!!jsonError || topic === ""} // Disable when JSON is invalid or topic is empty
                    >
                        Publish Message <IoSend className="ml-2" />
                    </button>
                </div>
            ) : (
                <button
                    className="btn text-[#fff] flex cursor-pointer items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={() => publish(brokerName, topic, dataToPublish)}
                    disabled={!!jsonError || topic === ""} // Disable when JSON is invalid or topic is empty
                >
                    Publish to {topic} <IoSend className="ml-2" />
                </button>
            )}
        </>
    );
};

export default Publish;
