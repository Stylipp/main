import { Box, type BoxProps } from '@mui/material'
import { motion, type MotionProps } from 'framer-motion'

type AnimatedBoxProps = BoxProps & MotionProps

export const AnimatedBox = motion.create(Box) as React.FC<AnimatedBoxProps>
