module.exports = {
  variants: {
    borderWidth: ['responsive', 'hover', 'focus', 'first']
  },
  theme: {
    extend: {
      borderWidth: {
        '1r': '0.25rem',
        '2r': '0.5rem'
      }
    }
  }
}
