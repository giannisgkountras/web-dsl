import { useState } from "react";
import ObjectEditor from "./ObjectEditor";
import { IoSend } from "react-icons/io5";
import { publish } from "../api/publish";
import { proxyRestCall } from "../api/proxyRestCall";
import { toast } from "react-toastify";

const Publish = ({ brokerName, apiName, destinationTopic, json, restData }) => {
    const [dataToPublish, setDataToPublish] = useState(
        json ? json : { key: "value" }
    );
    const [topic, setTopic] = useState("");
    const [jsonError, setJsonError] = useState(null);

    const postCall = () => {
        const { host, port, path, method, headers, params } = restData;

        proxyRestCall({
            host,
            port,
            path,
            method: "POST",
            headers,
            params,
            body: dataToPublish
        })
            .then((response) => {
                toast.success("Message published successfully!");
            })
            .catch((error) => {
                console.error("Error fetching initial value:", error);
            });
    };

    // If apiName prop exists, we assume the call is for an API
    if (apiName) {
        return (
            <>
                {/* If no JSON has been provided, let the user enter it via ObjectEditor */}
                {!json ? (
                    <div className="flex justify-center items-center flex-col w-full">
                        <h1 className="mb-2 text-lg font-semibold text-gray-200">
                            {apiName}
                        </h1>
                        <ObjectEditor
                            initialData={dataToPublish}
                            onChange={setDataToPublish}
                            jsonError={jsonError}
                            setJsonError={setJsonError}
                        />
                        <button
                            className="btn text-[#fff] flex cursor-pointer items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                            onClick={postCall}
                            disabled={!!jsonError}
                        >
                            Post to API <IoSend className="ml-2" />
                        </button>
                    </div>
                ) : (
                    // If a JSON payload is provided, simply show the button
                    <button
                        className="btn text-[#fff] flex cursor-pointer items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={postCall}
                        disabled={!!jsonError}
                    >
                        Post to API {apiName} <IoSend className="ml-2" />
                    </button>
                )}
            </>
        );
    }

    // Else, if brokerName exists, assume the call is for a broker
    if (brokerName) {
        return (
            <>
                {/* If destinationTopic or JSON is not provided, show the inputs */}
                {!destinationTopic || !json ? (
                    <div className="flex justify-center items-center flex-col w-full">
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
                            disabled={!!jsonError || topic === ""}
                        >
                            Publish Message <IoSend className="ml-2" />
                        </button>
                    </div>
                ) : (
                    // Otherwise, if a destinationTopic and JSON are provided, show just the button
                    <button
                        className="btn text-[#fff] flex cursor-pointer items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                        onClick={() =>
                            publish(brokerName, destinationTopic, json)
                        }
                        disabled={!!jsonError || destinationTopic === ""}
                    >
                        Publish to {destinationTopic}{" "}
                        <IoSend className="ml-2" />
                    </button>
                )}
            </>
        );
    }

    // Fallback in case neither brokerName nor apiName is provided
    return <h1>Error in given attributes</h1>;
};

export default Publish;
