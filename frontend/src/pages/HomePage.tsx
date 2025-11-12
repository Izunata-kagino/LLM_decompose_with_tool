import { Container, Typography, Box } from '@mui/material'

function HomePage() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          LLM Decompose Tool
        </Typography>
        <Typography variant="body1" color="text.secondary">
          A powerful interface for continuous LLM tool usage with parallel conversation support
        </Typography>
      </Box>
    </Container>
  )
}

export default HomePage
