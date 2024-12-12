import { useState, useEffect } from 'react';
import { Box, Button, CircularProgress } from '@mui/material';
import axios from 'axios';

 const HubSpotIntegration = ({ user, org, integrationParams, setIntegrationParams }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);

    // Request to backend to get HubSpot authorization URL
    const handleConnectClick = async () => {
        try {
            setIsConnecting(true);
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);

            // Send request to backend to get authorization URL
            const response = await axios.post('http://localhost:8000/integrations/hubspot/authorize', formData);
            const authURL = response?.data;
            
            // Open HubSpot authorization page in a new window
            const newWindow = window.open(authURL, 'HubSpot Authorization', 'width=600,height=600');
            
            // Polling the window to detect when it's closed
            const pollTimer = window.setInterval(() => {
                if (newWindow?.closed !== false) {
                    window.clearInterval(pollTimer);
                    handleWindowClosed();
                }
            }, 200);
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail || 'An error occurred');
        }
    };

    // When the HubSpot authorization window is closed, fetch credentials
    const handleWindowClosed = async () => {
        try {
            const formData = new FormData();
            formData.append('user_id', user);
            formData.append('org_id', org);
            
            // Fetch credentials after user authorizes HubSpot
            const response = await axios.post('http://localhost:8000/integrations/hubspot/credentials', formData);
            const credentials = response.data;
            
            if (credentials) {
                setIsConnecting(false);
                setIsConnected(true);
                setIntegrationParams(prev => ({ ...prev, credentials: credentials, type: 'HubSpot' }));
            }
        } catch (e) {
            setIsConnecting(false);
            alert(e?.response?.data?.detail || 'An error occurred while fetching credentials');
        }
    };

    // Effect to update connection state based on integration parameters
    useEffect(() => {
        setIsConnected(integrationParams?.credentials ? true : false);
    }, [integrationParams]);

    return (
        <Box sx={{ mt: 2 }}>
            <h3>HubSpot Integration</h3>
            <Box display='flex' alignItems='center' justifyContent='center' sx={{ mt: 2 }}>
                <Button
                    variant='contained'
                    onClick={isConnected ? () => {} : handleConnectClick}
                    color={isConnected ? 'success' : 'primary'}
                    disabled={isConnecting}
                    style={{
                        pointerEvents: isConnected ? 'none' : 'auto',
                        cursor: isConnected ? 'default' : 'pointer',
                        opacity: isConnected ? 1 : undefined
                    }}
                >
                    {isConnected ? 'HubSpot Connected' : isConnecting ? <CircularProgress size={20} /> : 'Connect to HubSpot'}
                </Button>
            </Box>
        </Box>
    );
};

export default HubSpotIntegration;