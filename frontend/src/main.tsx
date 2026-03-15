import { render } from "preact";
import { App } from "./App";
import "./styles.css";
import "uplot/dist/uPlot.min.css";

render(<App />, document.getElementById("root")!);
