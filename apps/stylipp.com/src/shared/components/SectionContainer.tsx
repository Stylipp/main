import { Container, type ContainerProps, styled } from '@mui/material'

export const SectionContainer = styled(Container)<ContainerProps>(() => ({
  paddingTop: 80,
  paddingBottom: 80,
  '@media (max-width:600px)': {
    paddingTop: 48,
    paddingBottom: 48,
  },
}))
