module.exports = {
  extends: [
    "plugin:vue/recommended",
    // "@vue/prettier"
  ],
  rules: {
    "no-console": "off",
    "no-debugger": "off",
    "indent": ["error", 2],
    "vue/max-attributes-per-line": "off"
    // "vue/max-attributes-per-line": ["error", {
    //   "singleline": 5,
    //   "multiline": {
    //     "max": 1,
    //     "allowFirstLine": false
    //   }
    // }]
  },
  // parserOptions: {
  //   parser: "babel-eslint"
  // }
}
