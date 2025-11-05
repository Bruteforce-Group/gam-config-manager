import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tantml/react-query'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
} from '@mui/material'
import { ArrowBack, Security as SecurityIcon, CompareArrows, CheckCircle, Error as ErrorIcon, Build as BuildIcon } from '@mui/icons-material'
import { configurationsApi, securityApi, comparisonsApi, remediationApi } from '@/services/api'

const ConfigurationDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState(0)
  const [compareDialogOpen, setCompareDialogOpen] = useState(false)
  const [compareTargetId, setCompareTargetId] = useState<number | ''>('')
  const [remediationDialogOpen, setRemediationDialogOpen] = useState(false)
  const [selectedRemediation, setSelectedRemediation] = useState<{findingId: number; actionId: string; label: string; parameters?: any} | null>(null)
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarMessage, setSnackbarMessage] = useState('')

  const { data: config, isLoading } = useQuery({
    queryKey: ['configuration', id],
    queryFn: () => configurationsApi.get(Number(id)).then((res) => res.data),
  })

  const { data: securityAnalyses } = useQuery({
    queryKey: ['security-analyses', id],
    queryFn: () => securityApi.getAnalyses(Number(id)).then((res) => res.data),
    enabled: !!config,
  })

  const { data: securityScore } = useQuery({
    queryKey: ['security-score', id],
    queryFn: () => securityApi.getScore(Number(id)).then((res) => res.data),
    enabled: !!config,
  })

  const { data: allConfigs } = useQuery({
    queryKey: ['configurations'],
    queryFn: () => configurationsApi.list().then((res) => res.data),
  })

  const analyzeMutation = useMutation({
    mutationFn: () => securityApi.analyze(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-analyses', id] })
      queryClient.invalidateQueries({ queryKey: ['security-score', id] })
    },
  })

  const compareMutation = useMutation({
    mutationFn: (targetId: number) =>
      comparisonsApi.create({
        source_config_id: Number(id),
        target_config_id: targetId,
      }),
    onSuccess: (response) => {
      setCompareDialogOpen(false)
      navigate(`/comparisons`)
    },
  })

  const remediationMutation = useMutation({
    mutationFn: (data: {findingId: number; actionId: string; parameters?: any}) =>
      remediationApi.execute({
        finding_id: data.findingId,
        action_id: data.actionId,
        parameters: data.parameters,
        auto_rescan: true
      }),
    onSuccess: (response) => {
      setRemediationDialogOpen(false)
      
      const message = response.finding_resolved 
        ? `✅ Issue fixed! Security score improved from ${response.security_score_before}/100 to ${response.security_score_after}/100`
        : `⚠️ Remediation executed but issue may still exist. Check the new configuration.`
      
      setSnackbarMessage(message)
      setSnackbarOpen(true)
      
      // Refresh data
      queryClient.invalidateQueries({ queryKey: ['security-analyses', id] })
      queryClient.invalidateQueries({ queryKey: ['security-score', id] })
      queryClient.invalidateQueries({ queryKey: ['configurations'] })
      
      // Navigate to new config if created
      if (response.new_configuration_id) {
        setTimeout(() => {
          navigate(`/configurations/${response.new_configuration_id}`)
        }, 2000)
      }
    },
    onError: () => {
      setSnackbarMessage('❌ Remediation failed. Please try manually.')
      setSnackbarOpen(true)
    }
  })

  const handleRemediationClick = (findingId: number, actionId: string, label: string, parameters?: any) => {
    setSelectedRemediation({findingId, actionId, label, parameters})
    setRemediationDialogOpen(true)
  }

  const executeRemediation = () => {
    if (selectedRemediation) {
      remediationMutation.mutate(selectedRemediation)
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!config) {
    return (
      <Box>
        <Alert severity="error">Configuration not found</Alert>
      </Box>
    )
  }

  const handleCompare = () => {
    if (compareTargetId) {
      compareMutation.mutate(Number(compareTargetId))
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error'
      case 'high':
        return 'warning'
      case 'medium':
        return 'info'
      case 'low':
        return 'success'
      default:
        return 'default'
    }
  }

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/configurations')} sx={{ mb: 2 }}>
        Back to Configurations
      </Button>

      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          {config.name}
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 2 }}>
          {config.description || 'No description'}
        </Typography>
        
        {/* Show extraction errors if any */}
        {config.extraction_errors && config.extraction_errors.errors && config.extraction_errors.errors.length > 0 && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Extraction completed with {config.extraction_errors.errors.length} error(s):
            </Typography>
            <Box component="ul" sx={{ mt: 1, mb: 0, pl: 2 }}>
              {config.extraction_errors.errors.map((error, idx) => (
                <Typography component="li" variant="body2" key={idx}>
                  {error}
                </Typography>
              ))}
            </Box>
          </Alert>
        )}
        
        {/* Extraction Summary - Show what was extracted */}
        {config.config_data && typeof config.config_data === 'object' && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Extraction Summary:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.keys(config.config_data).map((key) => {
                const data = config.config_data[key]
                const itemCount = Array.isArray(data) ? data.length : (typeof data === 'object' ? Object.keys(data).length : 1)
                const isEmpty = itemCount === 0 || (typeof data === 'string' && data.trim() === '')
                
                return (
                  <Chip
                    key={key}
                    icon={isEmpty ? <ErrorIcon /> : <CheckCircle />}
                    label={`${key}: ${itemCount} item${itemCount !== 1 ? 's' : ''}`}
                    color={isEmpty ? 'error' : 'success'}
                    size="small"
                    variant="outlined"
                  />
                )
              })}
              {/* Show failed types that weren't extracted at all */}
              {config.extraction_errors?.failed_types?.map((type) => (
                <Chip
                  key={type}
                  icon={<ErrorIcon />}
                  label={`${type}: failed`}
                  color="error"
                  size="small"
                  variant="filled"
                />
              ))}
            </Box>
          </Box>
        )}
        
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip label={config.config_type} />
          {config.is_template && <Chip label="Template" color="primary" />}
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<SecurityIcon />}
            onClick={() => analyzeMutation.mutate()}
            disabled={analyzeMutation.isPending}
          >
            Run Security Analysis
          </Button>
          <Button
            variant="outlined"
            startIcon={<CompareArrows />}
            onClick={() => setCompareDialogOpen(true)}
          >
            Compare with Another Config
          </Button>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tab} onChange={(_, newValue) => setTab(newValue)}>
          <Tab label="Configuration Data" />
          <Tab label={`Security Analysis ${securityAnalyses ? `(${securityAnalyses.length})` : ''}`} />
        </Tabs>
      </Box>

      {tab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configuration Data
            </Typography>
            <Box
              component="pre"
              sx={{
                p: 2,
                bgcolor: 'grey.100',
                borderRadius: 1,
                overflow: 'auto',
                maxHeight: '600px',
              }}
            >
              {JSON.stringify(config.config_data, null, 2)}
            </Box>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Box>
          {securityScore && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Security Score
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h3" color={securityScore.security_score > 70 ? 'success.main' : 'error.main'}>
                    {securityScore.security_score}
                  </Typography>
                  <Box>
                    <Typography variant="body2" color="textSecondary">
                      {securityScore.critical_findings} Critical, {securityScore.high_findings} High,{' '}
                      {securityScore.medium_findings} Medium, {securityScore.low_findings} Low
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

          {!securityAnalyses || securityAnalyses.length === 0 ? (
            <Card>
              <CardContent>
                <Typography color="textSecondary">
                  No security analysis available. Run an analysis to see recommendations.
                </Typography>
              </CardContent>
            </Card>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {securityAnalyses.map((analysis) => (
                <Card key={analysis.id}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Typography variant="h6">{analysis.title}</Typography>
                      <Chip label={analysis.severity} color={getSeverityColor(analysis.severity) as any} size="small" />
                    </Box>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      {analysis.description}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Recommendation:
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {analysis.recommendation}
                    </Typography>
                    {analysis.remediation_steps && analysis.remediation_steps.length > 0 && (
                      <>
                        <Typography variant="subtitle2" gutterBottom>
                          Remediation Steps:
                        </Typography>
                        <Box component="ol" sx={{ pl: 2, m: 0, mb: 2 }}>
                          {analysis.remediation_steps.map((step, idx) => (
                            <Typography component="li" variant="body2" key={idx}>
                              {step}
                            </Typography>
                          ))}
                        </Box>
                      </>
                    )}
                    {analysis.remediation_actions && analysis.remediation_actions.length > 0 && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          🔧 Auto-Fix Available:
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {analysis.remediation_actions.map((action, idx) => (
                            <Button
                              key={idx}
                              variant="contained"
                              size="small"
                              color="warning"
                              startIcon={<BuildIcon />}
                              onClick={() => handleRemediationClick(analysis.id, action.action_id, action.label, action.parameters)}
                            >
                              {action.label}
                            </Button>
                          ))}
                        </Box>
                        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                          Clicking will execute GAM command, re-extract config, and verify the fix
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Compare Dialog */}
      <Dialog open={compareDialogOpen} onClose={() => setCompareDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Compare Configuration</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Target Configuration</InputLabel>
            <Select
              value={compareTargetId}
              onChange={(e) => setCompareTargetId(e.target.value as number)}
              label="Target Configuration"
            >
              {allConfigs
                ?.filter((c) => c.id !== config.id)
                .map((c) => (
                  <MenuItem key={c.id} value={c.id}>
                    {c.name}
                  </MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompareDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCompare}
            disabled={!compareTargetId || compareMutation.isPending}
          >
            Compare
          </Button>
        </DialogActions>
      </Dialog>

      {/* Remediation Confirmation Dialog */}
      <Dialog open={remediationDialogOpen} onClose={() => !remediationMutation.isPending && setRemediationDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>🔧 Auto-Fix Security Issue</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
            This will automatically execute a GAM command to fix the security issue.
          </Alert>
          {selectedRemediation && (
            <>
              <Typography variant="subtitle2" gutterBottom>
                Action:
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedRemediation.label}
              </Typography>
              
              <Typography variant="subtitle2" gutterBottom>
                What will happen:
              </Typography>
              <Box component="ol" sx={{ pl: 2, m: 0 }}>
                <Typography component="li" variant="body2">
                  Execute GAM remediation command
                </Typography>
                <Typography component="li" variant="body2">
                  Re-extract the affected configuration
                </Typography>
                <Typography component="li" variant="body2">
                  Run security analysis on new config
                </Typography>
                <Typography component="li" variant="body2">
                  Verify the issue is resolved
                </Typography>
                <Typography component="li" variant="body2">
                  Show you the results
                </Typography>
              </Box>
            </>
          )}
          
          {remediationMutation.isPending && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <CircularProgress size={20} />
              <Typography variant="body2">
                Executing remediation and re-scanning...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRemediationDialogOpen(false)} disabled={remediationMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={executeRemediation}
            disabled={remediationMutation.isPending}
            startIcon={remediationMutation.isPending ? <CircularProgress size={16} /> : <BuildIcon />}
          >
            {remediationMutation.isPending ? 'Fixing...' : 'Execute Auto-Fix'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  )
}

export default ConfigurationDetail

