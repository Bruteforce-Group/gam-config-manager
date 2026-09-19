import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  CloudDownload,
  CompareArrows,
  Security,
  Description,
  CheckCircle,
  Pending,
  Error as ErrorIcon,
} from '@mui/icons-material'
import { configurationsApi, comparisonsApi, templatesApi, gamApi } from '@/services/api'
import { ConfigType } from '@/types'

interface ProgressUpdate {
  status: string
  message: string
  current_type?: string
  progress?: number
  configuration_id?: number
  errors?: string[]
}

const Dashboard = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [extractDialogOpen, setExtractDialogOpen] = useState(false)
  const [selectedTypes, setSelectedTypes] = useState<ConfigType[]>([
    ConfigType.USER,
    ConfigType.GROUP,
  ])
  const [saveAsTemplate, setSaveAsTemplate] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [isExtracting, setIsExtracting] = useState(false)
  const [progressUpdates, setProgressUpdates] = useState<ProgressUpdate[]>([])
  const [currentProgress, setCurrentProgress] = useState(0)
  const eventSourceRef = useRef<EventSource | null>(null)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true)

  // Fetch stats
  const { data: configs } = useQuery({
    queryKey: ['configurations'],
    queryFn: () => configurationsApi.list().then((res) => res.data),
  })

  const { data: comparisons } = useQuery({
    queryKey: ['comparisons'],
    queryFn: () => comparisonsApi.list().then((res) => res.data),
  })

  const { data: templates } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templatesApi.list().then((res) => res.data),
  })

  // Auto-scroll to bottom when new progress updates arrive
  useEffect(() => {
    if (shouldAutoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight
    }
  }, [progressUpdates, shouldAutoScroll])

  // Handle scroll events to detect manual scrolling
  const handleLogScroll = () => {
    if (!logContainerRef.current) return
    
    const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10
    
    setShouldAutoScroll(isAtBottom)
  }

  const handleExtract = () => {
    setShouldAutoScroll(true) // Reset auto-scroll for new extraction
    setIsExtracting(true)
    setProgressUpdates([])
    setCurrentProgress(0)
    
    // Build query params
    const params = new URLSearchParams({
      config_types: selectedTypes.join(','),
      save_as_template: saveAsTemplate.toString(),
    })
    if (saveAsTemplate && templateName) {
      params.append('template_name', templateName)
    }
    
    // Create EventSource for Server-Sent Events
    const eventSource = new EventSource(`/api/v1/gam/extract-stream?${params}`)
    eventSourceRef.current = eventSource
    
    eventSource.onmessage = (event) => {
      const update: ProgressUpdate = JSON.parse(event.data)
      
      // Add to progress updates
      setProgressUpdates(prev => [...prev, update])
      
      // Update progress bar
      if (update.progress !== undefined) {
        setCurrentProgress(update.progress)
      }
      
      // Handle completion
      if (update.status === 'complete') {
        setIsExtracting(false)
        eventSource.close()
        
        // Refresh configurations list
        queryClient.invalidateQueries({ queryKey: ['configurations'] })
        
        // Navigate to new configuration after a brief delay
        setTimeout(() => {
          setExtractDialogOpen(false)
          if (update.configuration_id) {
            navigate(`/configurations/${update.configuration_id}`)
          }
        }, 1500)
      }
      
      // Handle errors
      if (update.status === 'error' || update.status === 'partial_error') {
        setIsExtracting(false)
        eventSource.close()
      }
    }
    
    eventSource.onerror = () => {
      setIsExtracting(false)
      setProgressUpdates(prev => [...prev, {
        status: 'error',
        message: 'Connection error. Please try again.'
      }])
      eventSource.close()
    }
  }

  const handleTypeToggle = (type: ConfigType) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    )
  }

  const statsCards = [
    {
      title: 'Total Configurations',
      value: configs?.length || 0,
      icon: <CloudDownload fontSize="large" />,
      color: '#1976d2',
    },
    {
      title: 'Comparisons',
      value: comparisons?.length || 0,
      icon: <CompareArrows fontSize="large" />,
      color: '#2e7d32',
    },
    {
      title: 'Templates',
      value: templates?.length || 0,
      icon: <Description fontSize="large" />,
      color: '#ed6c02',
    },
    {
      title: 'Drift Detected',
      value: comparisons?.filter((c) => c.drift_detected).length || 0,
      icon: <Security fontSize="large" />,
      color: '#d32f2f',
    },
  ]

  const recentConfigs = configs?.slice(0, 5) || []

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">Dashboard</Typography>
        <Button
          variant="contained"
          startIcon={<CloudDownload />}
          onClick={() => setExtractDialogOpen(true)}
        >
          Extract Configuration
        </Button>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statsCards.map((card) => (
          <Grid item xs={12} sm={6} md={3} key={card.title}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4">{card.value}</Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Recent Configurations */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Recent Configurations
          </Typography>
          {recentConfigs.length === 0 ? (
            <Typography color="textSecondary">
              No configurations yet. Extract one from GAM to get started.
            </Typography>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {recentConfigs.map((config) => (
                <Box
                  key={config.id}
                  sx={{
                    p: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                  }}
                  onClick={() => navigate(`/configurations/${config.id}`)}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="subtitle1">{config.name}</Typography>
                      <Typography variant="body2" color="textSecondary">
                        {config.description || 'No description'}
                      </Typography>
                    </Box>
                    <Box>
                      <Chip label={config.config_type} size="small" sx={{ mr: 1 }} />
                      {config.is_template && <Chip label="Template" size="small" color="primary" />}
                    </Box>
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Extract Dialog */}
      <Dialog 
        open={extractDialogOpen} 
        onClose={() => !isExtracting && setExtractDialogOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>Extract GAM Configuration</DialogTitle>
        <DialogContent>
          {isExtracting && (
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" color="textSecondary">
                  Extracting configuration...
                </Typography>
                <Typography variant="body2" color="primary" fontWeight="bold">
                  {currentProgress}%
                </Typography>
              </Box>
              <LinearProgress variant="determinate" value={currentProgress} sx={{ mb: 2 }} />
              
              {progressUpdates.length > 0 && (
                <Card 
                  variant="outlined" 
                  sx={{ 
                    maxHeight: 192, // ~4 lines (48px each for dense list items)
                    overflow: 'auto', 
                    bgcolor: 'grey.50',
                    '&::-webkit-scrollbar': {
                      width: '8px',
                    },
                    '&::-webkit-scrollbar-thumb': {
                      backgroundColor: 'rgba(0,0,0,0.2)',
                      borderRadius: '4px',
                    },
                  }}
                  ref={logContainerRef}
                  onScroll={handleLogScroll}
                >
                  <List dense>
                    {progressUpdates.map((update, idx) => (
                      <ListItem key={idx}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          {update.status === 'complete' || update.status === 'completed_type' ? (
                            <CheckCircle color="success" fontSize="small" />
                          ) : update.status.includes('error') ? (
                            <ErrorIcon color="error" fontSize="small" />
                          ) : (
                            <Pending color="primary" fontSize="small" />
                          )}
                        </ListItemIcon>
                        <ListItemText 
                          primary={update.message}
                          primaryTypographyProps={{ 
                            variant: 'body2',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem'
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Card>
              )}
            </Box>
          )}
          
          {!isExtracting && progressUpdates.some(u => u.status.includes('error')) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              Extraction failed. Please check your GAM setup and try again.
            </Alert>
          )}

          <FormControl component="fieldset" sx={{ mt: 2, mb: 2 }}>
            <FormLabel component="legend">Configuration Types</FormLabel>
            <FormGroup>
              {Object.values(ConfigType).map((type) => (
                <FormControlLabel
                  key={type}
                  control={
                    <Checkbox
                      checked={selectedTypes.includes(type)}
                      onChange={() => handleTypeToggle(type)}
                    />
                  }
                  label={type.replace('_', ' ').toUpperCase()}
                />
              ))}
            </FormGroup>
          </FormControl>

          <FormControlLabel
            control={
              <Checkbox
                checked={saveAsTemplate}
                onChange={(e) => setSaveAsTemplate(e.target.checked)}
              />
            }
            label="Save as template"
          />

          {saveAsTemplate && (
            <TextField
              fullWidth
              label="Template Name"
              value={templateName}
              onChange={(e) => setTemplateName(e.target.value)}
              sx={{ mt: 2 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExtractDialogOpen(false)} disabled={isExtracting}>
            {isExtracting ? 'Close' : 'Cancel'}
          </Button>
          <Button
            variant="contained"
            onClick={handleExtract}
            disabled={selectedTypes.length === 0 || isExtracting}
            startIcon={isExtracting && <CircularProgress size={20} />}
          >
            {isExtracting ? 'Extracting...' : 'Extract'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default Dashboard

