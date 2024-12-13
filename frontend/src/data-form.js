import { useState, useEffect } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';
import { z } from 'zod';

const emailSchema = z.string().email();

const validateEmail = (email) => {
    try {
        emailSchema.parse(email);
        return true;
    } catch (error) {
        return false;
    }
};

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const [currentQueryUserEmail, setCurrentQueryUserEmail] = useState(null);
    const endpoint = endpointMapping[integrationType];
    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            const data = response.data;
            // console.log(data);
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    };

    useEffect(() => {
        handleLoad();
    }, []); // Run once on component mount


    const handleQueryUser = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));

            if (validateEmail(currentQueryUserEmail)) {
                formData.append('query_user_email', currentQueryUserEmail);
                const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/query`, formData);
                const data = response.data;
                // console.log(data);
                setLoadedData(data);
            } else {
                setCurrentQueryUserEmail("Enter a valid email")
            }
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    };



    // A string representation for each object in loadedData
    let dataString;

    try {
        dataString = loadedData && loadedData.length > 0
            ? loadedData.map((item) => {
                const idString = item.id && item.id !== null ? `Id: ${item.id}\n` : '';
                const nameString = `Name: ${item.name || ''}\n`;
                const emailString = item.email && item.email !== null ? `Email: ${item.email}\n` : '';
                const hsObjectId = item.hs_object_id && item.hs_object_id !== null ? `HubSpot Object ID: ${item.hs_object_id}\n` : ``;
                const createdate = item.create_date && item.create_date !== null ? `Create Date: ${item.create_date}` : ``;
                return hsObjectId + idString + nameString + emailString + createdate;
            }).join('\n------------------------------------------------------\n'):'';
    } catch (error) {
        dataString = 'Oops! Some error occurred while fetching your data';
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
                <TextField
                    label="Loaded Data"
                    multiline
                    value={dataString || ''}
                    sx={{
                        mt: 2,
                        width: '50%'
                    }}
                    InputLabelProps={{ shrink: true }}
                    disabled
                />
                <Button
                    onClick={handleLoad}
                    sx={{
                        mt: 2,
                        width: '10%',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{
                        mt: 1,
                        width: '10%',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}
                    variant='contained'
                >
                    Clear Data
                </Button>
                {
                    integrationType === 'HubSpot' && (
                        <>
                            <TextField
                                label="Get User Details"
                                value={currentQueryUserEmail}
                                sx={{
                                    mt: 2,
                                    width: '20%'
                                }}
                                onChange={(e) => setCurrentQueryUserEmail(e.target.value)}
                            />
                            <Button
                                onClick={handleQueryUser}
                                sx={{
                                    mt: 1,
                                    width: '10%',
                                    justifyContent: 'center',
                                    alignItems: 'center'
                                }}
                                variant='contained'
                            >
                                Get Details
                            </Button>
                        </>
                    )
                }
            </Box>
        </Box>
    );
}
