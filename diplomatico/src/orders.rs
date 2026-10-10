pub(crate) struct Move {
    pub(crate) dst: u16,
}

pub(crate) struct Convoyed {
    pub(crate) dst: u16,
    pub(crate) routes: Vec<Vec<u16>>
}

pub(crate) struct SupportHold {
    pub(crate) dst: u16,
}

pub(crate) struct SupportMove {
    pub(crate) src: u16,
    pub(crate) dst: u16,
}

pub(crate) struct Convoyer {
    pub(crate) src: u16,
    pub(crate) dst: u16,
}

pub(crate) enum OrderData {
    Hold,
    Move(Move),
    MoveViaConvoy(Convoyed),
    SupportHold(SupportHold),
    SupportMove(SupportMove),
    Convoy(Convoyer),
}

pub(crate) struct Order {
    pub(crate) territory: u16,
    pub(crate) country: String,
    pub(crate) data: OrderData,
    pub(crate) failed: bool,
}
