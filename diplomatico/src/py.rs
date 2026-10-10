use pyo3::{exceptions::PyValueError, prelude::*, types::PyDict};

use crate::adjudicate::adjudicate;
use crate::orders::{Convoyed, Convoyer, Move, Order, OrderData, SupportHold, SupportMove};

macro_rules! dict_item {
    ($py: expr, $dict: expr, $key: expr, $ty: ty) => {
        if let Ok(Some(pv)) = $dict.get_item(pyo3::intern!($py, $key)) {
            pv.extract::<$ty>()
        } else {
            Err(PyValueError::new_err($key))
        }
    };
    (def $py: expr, $dict: expr, $key: expr, $ty: ty, $def: expr) => {
        if let Ok(Some(pv)) = $dict.get_item(pyo3::intern!($py, $key)) {
            pv.extract::<$ty>().unwrap_or($def)
        } else {
            $def
        }
    };
}

macro_rules! build_order {
    ($py: expr, $pydata: expr, $data: expr) => {{
        let id = dict_item!($py, $pydata, "id", u16)?;
        let country = dict_item!($py, $pydata, "country", String)?;
        let failed = dict_item!($py, $pydata, "failed", bool)?;
        Order { territory: id, country: country, data: $data, failed }
    }};
}


#[pyfunction]
#[pyo3(signature = (orders))]
pub(super) fn solve_diplomacy<'p>(py: Python<'p>, orders: Vec<Bound<'p, PyDict>>) -> PyResult<Vec<Bound<'p, PyDict>>> {
    let mut stack = vec![];

    for item in &orders {
        if let Ok(Some(order_pytype)) = item.get_item(pyo3::intern!(py, "type")) {
            if let Ok(order_type) = order_pytype.extract::<i32>() {
                match order_type {
                    0 => {
                        let order = build_order!(py, item, OrderData::Hold);
                        stack.push(order);
                    },
                    1 => {
                        let odata = if dict_item!(def py, item, "through", bool, false) {
                            OrderData::MoveViaConvoy(Convoyed { dst: dict_item!(py, item, "dst", u16)?, routes: dict_item!(py, item, "routes", Vec<Vec<u16>>)? })
                        } else {
                            OrderData::Move(Move { dst: dict_item!(py, item, "dst", u16)? })
                        };
                        let order = build_order!(py, item, odata);
                        stack.push(order);
                    },
                    2 => {
                        let odata = OrderData::SupportHold(SupportHold { dst: dict_item!(py, item, "dst", u16)? });
                        let order = build_order!(py, item, odata);
                        stack.push(order);
                    },
                    3 => {
                        let odata = OrderData::SupportMove(SupportMove { src: dict_item!(py, item, "src", u16)?, dst: dict_item!(py, item, "dst", u16)? });
                        let order = build_order!(py, item, odata);
                        stack.push(order);
                    },
                    4 => {
                        let odata = OrderData::Convoy(Convoyer { src: dict_item!(py, item, "src", u16)?, dst: dict_item!(py, item, "dst", u16)? });
                        let order = build_order!(py, item, odata);
                        stack.push(order);
                    },
                    _ => {}
                }
            }
        }
    }

    let mut ret = vec![];
    for verdict in adjudicate(&stack)? {
        let dict = PyDict::new(py);
        dict.set_item(pyo3::intern!(py, "id"), verdict.territory)?;
        dict.set_item(pyo3::intern!(py, "succeeded"), verdict.succeeded)?;
        dict.set_item(pyo3::intern!(py, "dislodged"), verdict.dislodged)?;
        ret.push(dict);
    }
    Ok(ret)
}
