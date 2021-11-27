import React, { useEffect, useState } from 'react'
import '../App.css';

export default function EndpointAudit(props) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [log, setLog] = useState(null);
    const [error, setError] = useState(null)
	const rand_val = Math.floor(Math.random() * 100); // Get a random event from the event store
    const [index, setIndex] = useState(null); //Add a state for the index to display Audit Log index and the corresponding Event *9
    
    const getAudit = () => {
        fetch(`http://microservice-jasleen-new.eastus.cloudapp.azure.com:8200/${props.endpoint}?index=${rand_val}`) // Change the URL to that of your Cloud VM
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Audit Results for " + props.endpoint)
                setLog(result);
                setIsLoaded(true);
                setIndex(rand_val); //Set the index upon successfully response from the audit endpoints *9
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
	useEffect(() => {
		const interval = setInterval(() => getAudit(), 4000); // Update every 4 seconds
		return() => clearInterval(interval);
    }, [getAudit]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        
        return (
            <div>
                {/* <h3>{props.endpoint}-{rand_val}</h3> */}
                <h3>{props.endpoint}-{index}</h3>
                {JSON.stringify(log)}
            </div>
        )
    }
}
