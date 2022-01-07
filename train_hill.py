from game.hill_model import HillClimberModel


if __name__ == '__main__':
    model = HillClimberModel(restore=True)
    model.train(5000)
