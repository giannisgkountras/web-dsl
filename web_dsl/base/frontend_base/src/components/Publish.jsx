import JsonView from "@uiw/react-json-view";
import { useState } from "react";
import ObjectEditor from "./ObjectEditor";
import { IoSend } from "react-icons/io5";
import { publish } from "../api/publish";

const Publish = ({ brokerName }) => {
    const [dataToPublish, setDataToPublish] = useState({});
    const [topic, setTopic] = useState("");

    return (
        <div className="flex justify-between items-center w-full">
            <div className="flex justify-center items-center flex-col">
                <h1 className="font-bold">{brokerName}</h1>
                <p>Enter the topic:</p>
                <input
                    type="text"
                    onChange={(e) => {
                        setTopic(e.target.value);
                    }}
                    placeholder="Topic"
                ></input>
                <ObjectEditor
                    initialData={dataToPublish}
                    onChange={setDataToPublish}
                />
            </div>
            <div className="flex justify-center items-center flex-col bg-gray-800 p-4 rounded-lg">
                <p className="mt-2">Data to send:</p>
                <pre className="p-2 rounded">
                    {JSON.stringify(dataToPublish, null, 2)}
                </pre>
                <button
                    className="btn text-[#fff] flex items-center justify-center"
                    onClick={() => {
                        publish(brokerName, topic, dataToPublish);
                    }}
                >
                    Publish Message <IoSend className="ml-2" />
                </button>
            </div>
        </div>
    );
};

export default Publish;
