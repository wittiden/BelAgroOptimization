from app.database.engine import session_factory
from app.modules.repository.mapper import ModelDataMapper
from app.modules.model.opt_model import BelarusAgroModel
from app.modules.repository.queries import AgroQueriesRepository


def main():


    with session_factory() as session:
        repo = AgroQueriesRepository(session)
        mapper = ModelDataMapper(repo)

        model_data = mapper.build_from_active_scenario()
        model = BelarusAgroModel(model_data)

        if model.solve():
            model.print_results()
            model.create_plots('./plots')


if __name__ == "__main__":
    main()