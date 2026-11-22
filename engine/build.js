// The engine's modules see each other through one closure: the sources are
// joined in this order and compiled as a single input, not one by one.
import { dirname } from "node:path";
import CoffeeScript from "coffeescript";

const SOURCES = [
  "base/translator.coffee",
  "game/proto.coffee",
  "game/constants.coffee",
  "game/objects.coffee",
  "game/steps.coffee",
  "game/net.coffee",
  "game/env.coffee",
  "game/game.coffee",
  "game/board.coffee",
  "game/interactions.coffee",
  "game/ux.coffee",
  "game/utils.coffee",
  "game/main.coffee",
];
const ROOT = new URL("../diplomatic/assets/", import.meta.url);

const [output] = Deno.args;
const source = SOURCES.map((path) => Deno.readTextFileSync(new URL(path, ROOT))).join("\n");
Deno.mkdirSync(dirname(output), { recursive: true });
Deno.writeTextFileSync(output, CoffeeScript.compile(source));
