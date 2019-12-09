export const ListMapper = () => ({
  data: [],
  _build_element(data, idx) {
    let self = this
    let obj = {
      ...data,
      idx: idx,
      prev() {
        return self.get(this.idx - 1)
      },
      next() {
        return self.get(this.idx + 1)
      }
    }
    return obj
  },
  append(element) {
    let { length: idx } = this.data
    this.data.push(this._build_element(element, idx))
  },
  insert(idx, element) {
    let { length: len } = this.data
    this.data.slice(idx, len).forEach((item) => {
      item.idx += 1
    })
    this.data.splice(idx, 0, this._build_element(element, idx))
  },
  get(idx) {
    let { length: len } = this.data
    if (idx < 0) {
      idx = (len + idx)
    }
    return (0 <= idx && idx < len) ? this.data[idx] : null
  },
  slice(start, end) {
    return this.data.slice(start, end)
  },
  len() {
    return this.data.length
  },
  first() {
    return this.get(0)
  },
  last() {
    return this.get(-1)
  }
})

export const buildGameStep = (mapData, gameData, data, orders=null, isLast=false) => {
  let types = {
    0: 'diplomacy',
    1: 'retreats',
    2: 'builds'
  }
  let rv = {
    id: data.id,
    type: types[data.type],
    parent: data.parent,
    isLast: isLast,
    supply_centers: {},
    troops: {},
    orders: orders,
    data: data,
    label() {
      let types = {
        retreats: 'Retreats',
        builds: 'Builds'
      }
      let seasons = {
        0: 'Autumn',
        1: 'Spring'
      }
      if (this.type == 'diplomacy') {
        return `${seasons[this.data.season]} ${this.data.year}`
      }
      return `${types[this.type]} ${this.data.year}`
    }
  }
  gameData.players.forEach((key) => {
    rv.supply_centers[key] = 0
    data.territories[key].forEach((value) => {
      if (value in mapData.supply_centers) {
        rv.supply_centers[key] += 1
      }
    })
    rv.troops[key] = {
      armies: ((data.troops[key] || {}).armies || []).length,
      fleets: ((data.troops[key] || {}).fleets || []).length
    }
  })
  if (orders !== null) {
    gameData.players.forEach((key) => {
      rv.orders[key] = orders[key] || []
    })
  }
  return rv
}

export const buildPreGameStep = (mapData, gameData) => {
  let rv = {
    id: null,
    type: 'pre',
    parent: null,
    isLast: false,
    supply_centers: {},
    troops: {},
    orders: {},
    data: {
      territories: {},
      troops: {},
      coasts: {},
      dislodged: {}
    },
    label() {
      return 'Pre Game'
    }
  }
  gameData.players.forEach((key) => {
    rv.data.territories[key] = mapData.init.territories[key]
    rv.supply_centers[key] = mapData.home_centers[key].length
    rv.troops[key] = {armies: 0, fleets: 0}
    rv.orders[key] = []
  })
  return rv
}

export const buildNextGameStep = (player, prevStep) => {
  let rv = {
    id: null,
    type: 'next',
    parent: prevStep.id,
    isLast: false,
    supply_centers: { ...prevStep.supply_centers },
    troops: { ...prevStep.troops },
    orders: {},
    data: {
      territories: prevStep.data.territories,
      troops: prevStep.data.troops,
      coasts: prevStep.data.coasts,
      dislodged: prevStep.data.dislodged
    },
    label() {
      return 'Next'
    }
  }
  rv.orders[player] = []
  console.log(rv)
  return rv
}

const _componentToHex = (c) => {
  let hex = c.toString(16)
  if (hex.length == 1) {
    return `0${hex}`
  }
  return hex
}

export const rgbToHex = (r, g, b) => {
  return `#${_componentToHex(r)}${_componentToHex(g)}${_componentToHex(b)}`
}
