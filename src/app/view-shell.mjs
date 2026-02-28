export class ViewShell {
  constructor(controller) {
    if (!controller) {
      throw new Error("ViewShell requires a playback controller");
    }

    this.controller = controller;
    this.currentView = "list";
  }

  switchView(view) {
    if (view !== "list" && view !== "now-playing") {
      throw new Error("view must be list or now-playing");
    }
    this.currentView = view;
    return this.getState();
  }

  getState() {
    return {
      view: this.currentView,
      playback: this.controller.getState()
    };
  }
}
